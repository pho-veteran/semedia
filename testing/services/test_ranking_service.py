from __future__ import annotations

import pytest

from semedia_shared.ranking_service import (
    _apply_diversity,
    _apply_reranking,
    _calibrate_scores,
    build_result_explanation,
    merge_candidates,
    rank_candidates,
)


@pytest.fixture
def test_settings(tmp_path):
    from semedia_shared.config import Settings

    return Settings(
        service_name="test",
        database_url=f"sqlite:///{(tmp_path / 'test.sqlite3').resolve().as_posix()}",
        media_root=tmp_path / "media",
        media_base_url="/media",
        log_level="INFO",
        log_format="text",
        clip_model_name="openai/clip-vit-base-patch32",
        caption_model_name="Salesforce/blip-image-captioning-base",
        scene_detection_threshold=27.0,
        search_vector_weight=0.7,
        search_keyword_weight=0.3,
        search_max_results=20,
        search_max_per_media=2,
        ml_device="cpu",
        ml_strict_cuda=False,
        ml_preload_models=False,
        media_worker_url="http://worker.test",
        search_api_url="http://search.test",
        allow_all_origins=True,
        caption_max_length=50,
        caption_min_length=10,
        caption_num_beams=5,
        caption_retry_weak=True,
        caption_retry_num_beams=8,
        caption_batch_size=8,
        caption_retry_fallback="Image content unclear.",
        caption_weak_min_words=3,
        caption_weak_min_chars=10,
        caption_retry_max_length=60,
        caption_retry_min_length=15,
    )


def test_merge_candidates_preserves_vector_and_keyword_scores():
    vector_results = [
        {"key": ("image", 1), "media_id": 1, "caption": "cat", "score": 0.9},
        {"key": ("image", 2), "media_id": 2, "caption": "dog", "score": 0.7},
    ]
    keyword_results = [
        {"key": ("image", 1), "media_id": 1, "caption": "cat", "score": 0.5},
        {"key": ("image", 3), "media_id": 3, "caption": "bird", "score": 0.6},
    ]

    merged = merge_candidates(vector_results, keyword_results)

    assert len(merged) == 3
    cat_item = next(item for item in merged if item["media_id"] == 1)
    assert cat_item["vector_score"] == 0.9
    assert cat_item["keyword_score"] == 0.5

    dog_item = next(item for item in merged if item["media_id"] == 2)
    assert dog_item["vector_score"] == 0.7
    assert dog_item["keyword_score"] == 0.0

    bird_item = next(item for item in merged if item["media_id"] == 3)
    assert bird_item["vector_score"] == 0.0
    assert bird_item["keyword_score"] == 0.6


def test_apply_reranking_boosts_exact_phrase_match(test_settings):
    candidates = [
        {"media_id": 1, "caption": "office desk workspace laptop", "original_filename": "img1.jpg", "fusion_score": 0.5},
        {"media_id": 2, "caption": "workspace with laptop and chair", "original_filename": "img2.jpg", "fusion_score": 0.5},
    ]

    reranked = _apply_reranking(test_settings, candidates, "office desk")

    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]
    assert reranked[0]["media_id"] == 1


def test_apply_reranking_ignores_filename_token_match(test_settings):
    candidates = [
        {"media_id": 1, "caption": "workspace scene", "original_filename": "office-meeting-room.jpg", "fusion_score": 0.5},
        {"media_id": 2, "caption": "workspace scene", "original_filename": "random-image.jpg", "fusion_score": 0.5},
    ]

    reranked = _apply_reranking(test_settings, candidates, "office")

    assert reranked[0]["rerank_score"] == reranked[1]["rerank_score"] == 0.5


def test_apply_reranking_boosts_rich_captions(test_settings):
    candidates = [
        {"media_id": 1, "caption": "red sofa in bright living room with large windows and warm sunlight", "original_filename": "img1.jpg", "fusion_score": 0.5},
        {"media_id": 2, "caption": "sofa", "original_filename": "img2.jpg", "fusion_score": 0.5},
    ]

    reranked = _apply_reranking(test_settings, candidates, "sofa")

    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]
    assert reranked[0]["media_id"] == 1


def test_apply_diversity_limits_scenes_per_video(test_settings):
    candidates = [
        {"media_id": 1, "scene_id": 1, "caption": "scene 1", "rerank_score": 0.9},
        {"media_id": 1, "scene_id": 2, "caption": "scene 2", "rerank_score": 0.85},
        {"media_id": 1, "scene_id": 3, "caption": "scene 3", "rerank_score": 0.8},
        {"media_id": 2, "scene_id": 4, "caption": "other scene", "rerank_score": 0.7},
    ]

    diversified = _apply_diversity(test_settings, candidates, limit=10, dedupe_captions=False)

    media_1_count = sum(1 for item in diversified if item["media_id"] == 1)
    assert media_1_count == 2


def test_apply_diversity_preserves_top_scene_from_video(test_settings):
    candidates = [
        {"media_id": 1, "scene_id": 1, "caption": "scene 1", "rerank_score": 0.9},
        {"media_id": 1, "scene_id": 2, "caption": "scene 2", "rerank_score": 0.85},
        {"media_id": 1, "scene_id": 3, "caption": "scene 3", "rerank_score": 0.8},
    ]

    diversified = _apply_diversity(test_settings, candidates, limit=10, dedupe_captions=False)

    assert diversified[0]["scene_id"] == 1
    assert diversified[1]["scene_id"] == 2


def test_apply_diversity_deduplicates_captions_when_enabled(test_settings):
    candidates = [
        {"media_id": 1, "caption": "there is a man that is standing in the dark with a bat", "rerank_score": 0.9},
        {"media_id": 2, "caption": "there is a man that is standing in the dark with a bat", "rerank_score": 0.85},
        {"media_id": 3, "caption": "moonlit lake water by a pier", "rerank_score": 0.8},
    ]

    diversified = _apply_diversity(test_settings, candidates, limit=10, dedupe_captions=True)

    assert len(diversified) == 2
    captions = [item["caption"] for item in diversified]
    assert captions.count("there is a man that is standing in the dark with a bat") == 1


def test_calibrate_scores_returns_normalized_range():
    candidates = [
        {"rerank_score": 0.95},
        {"rerank_score": 0.5},
        {"rerank_score": 1.2},
        {"rerank_score": -0.1},
    ]

    calibrated = _calibrate_scores(candidates)

    assert all(0.0 <= item["score"] <= 1.0 for item in calibrated)
    assert calibrated[0]["score"] == 0.95
    assert calibrated[1]["score"] == 0.5
    assert calibrated[2]["score"] == 1.0
    assert calibrated[3]["score"] == 0.0


def test_rank_candidates_text_mode_applies_fusion_and_reranking(test_settings):
    candidates = [
        {
            "key": ("image", 1),
            "media_id": 1,
            "caption": "office desk workspace laptop",
            "original_filename": "office.jpg",
            "vector_score": 0.6,
            "keyword_score": 0.8,
        },
        {
            "key": ("image", 2),
            "media_id": 2,
            "caption": "random scene",
            "original_filename": "random.jpg",
            "vector_score": 0.7,
            "keyword_score": 0.5,
        },
    ]

    ranked = rank_candidates(test_settings, candidates, query_text="office desk", query_mode="text", limit=10)

    assert ranked[0]["media_id"] == 1
    assert 0.0 <= ranked[0]["score"] <= 1.0
    assert ranked[0]["score"] > ranked[1]["score"]


def test_rank_candidates_image_mode_uses_vector_only(test_settings):
    candidates = [
        {
            "key": ("image", 1),
            "media_id": 1,
            "caption": "cat",
            "original_filename": "cat.jpg",
            "vector_score": 0.9,
            "keyword_score": 0.0,
        },
        {
            "key": ("image", 2),
            "media_id": 2,
            "caption": "dog",
            "original_filename": "dog.jpg",
            "vector_score": 0.7,
            "keyword_score": 0.0,
        },
    ]

    ranked = rank_candidates(test_settings, candidates, query_text=None, query_mode="image", limit=10)

    assert ranked[0]["media_id"] == 1
    assert 0.0 <= ranked[0]["score"] <= 1.0
    assert ranked[0]["score"] > ranked[1]["score"]



def test_apply_reranking_stacks_multiple_boosts_and_clamps(test_settings):
    candidates = [
        {
            "media_id": 1,
            "caption": "office desk workspace laptop with bright window light and conference notebooks",
            "original_filename": "office-desk-photo.jpg",
            "fusion_score": 0.95,
        }
    ]

    reranked = _apply_reranking(test_settings, candidates, "office desk")

    assert reranked[0]["rerank_score"] == 1.0



def test_rank_candidates_handles_equal_scores_without_malformed_output(test_settings):
    candidates = [
        {
            "key": ("image", 1),
            "media_id": 1,
            "caption": "same caption one",
            "original_filename": "one.jpg",
            "vector_score": 0.5,
            "keyword_score": 0.5,
        },
        {
            "key": ("image", 2),
            "media_id": 2,
            "caption": "same caption two",
            "original_filename": "two.jpg",
            "vector_score": 0.5,
            "keyword_score": 0.5,
        },
    ]

    ranked = rank_candidates(test_settings, candidates, query_text="neutral", query_mode="image", limit=10)

    assert len(ranked) == 2
    assert all(0.0 <= item["score"] <= 1.0 for item in ranked)
    assert ranked[0]["score"] == ranked[1]["score"] == 0.5
    assert {item["media_id"] for item in ranked} == {1, 2}


def test_build_result_explanation_marks_caption_match(test_settings):
    candidate = {
        "caption": "office desk",
        "vector_score": 0.3,
        "keyword_score": 1.0,
        "fusion_score": 0.51,
        "rerank_score": 0.59,
    }

    explanation = build_result_explanation(candidate, query_text="office desk", query_mode="text")

    assert explanation == {
        "match_type": "caption",
        "exact_phrase_match": True,
        "rich_caption": False,
        "rerank_boost": 0.08,
    }


def test_build_result_explanation_marks_hybrid_match_with_rich_caption(test_settings):
    candidate = {
        "caption": "office desk workspace laptop with bright window light and conference notebooks",
        "vector_score": 0.8,
        "keyword_score": 0.4,
        "fusion_score": 0.68,
        "rerank_score": 0.78,
    }

    explanation = build_result_explanation(candidate, query_text="office desk", query_mode="text")

    assert explanation == {
        "match_type": "hybrid",
        "exact_phrase_match": True,
        "rich_caption": True,
        "rerank_boost": 0.1,
    }


def test_build_result_explanation_marks_image_results_as_visual(test_settings):
    candidate = {
        "caption": "a red square",
        "vector_score": 0.9,
        "keyword_score": 0.0,
        "fusion_score": 0.9,
        "rerank_score": 0.9,
    }

    explanation = build_result_explanation(candidate, query_text=None, query_mode="image")

    assert explanation == {
        "match_type": "visual",
        "exact_phrase_match": False,
        "rich_caption": False,
        "rerank_boost": 0.0,
    }
