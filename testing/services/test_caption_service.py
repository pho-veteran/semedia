from __future__ import annotations

import sys
from pathlib import Path

import pytest

SEMEDIA_ROOT = Path(__file__).resolve().parents[2]
SHARED_PATH = SEMEDIA_ROOT / "services" / "shared"

if str(SHARED_PATH) not in sys.path:
    sys.path.insert(0, str(SHARED_PATH))

from semedia_shared.caption_service import _clean_caption, _is_weak_caption
from semedia_shared.config import Settings


@pytest.fixture
def test_settings(tmp_path):
    return Settings(
        service_name="test",
        database_url="sqlite:///:memory:",
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
        ml_device="cpu",
        ml_strict_cuda=False,
        ml_preload_models=False,
        media_worker_url="http://test",
        search_api_url="http://test",
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


def test_is_weak_caption_rejects_generic(test_settings):
    assert _is_weak_caption(test_settings, "an image")
    assert _is_weak_caption(test_settings, "a picture of something")
    assert _is_weak_caption(test_settings, "unclear")
    assert _is_weak_caption(test_settings, "a photo")
    assert _is_weak_caption(test_settings, "image content unclear")


def test_is_weak_caption_accepts_awkward_but_useful_descriptions(test_settings):
    assert not _is_weak_caption(test_settings, "there is a dog that is laying down on the floor")
    assert not _is_weak_caption(test_settings, "there are people in a room")
    assert not _is_weak_caption(test_settings, "arafed pier on a lake with a full moon in the background")
    assert not _is_weak_caption(test_settings, "a close up of a red background with a white border")


def test_clean_caption_removes_malformed_prefix_noise():
    assert _clean_caption("arafed pier on a lake with a full moon in the background") == "Pier on a lake with a full moon."
    assert _clean_caption("this is a black and white photo of an airplane flying in the sky") == "Black and white airplane flying in the sky."




def test_is_weak_caption_rejects_short(test_settings):
    assert _is_weak_caption(test_settings, "cat")
    assert _is_weak_caption(test_settings, "a dog")
    assert _is_weak_caption(test_settings, "")
    assert _is_weak_caption(test_settings, "ab")


def test_is_weak_caption_accepts_descriptive(test_settings):
    assert not _is_weak_caption(test_settings, "a golden retriever running in a park")
    assert not _is_weak_caption(test_settings, "sunset over the ocean with waves")
    assert not _is_weak_caption(test_settings, "person sitting at desk")


def test_clean_caption_normalizes_whitespace():
    assert _clean_caption("  a   dog  ") == "A dog."


def test_clean_caption_adds_period():
    assert _clean_caption("a cat on a table") == "A cat on a table."


def test_clean_caption_capitalizes():
    assert _clean_caption("golden retriever") == "Golden retriever."


def test_clean_caption_preserves_existing_punctuation():
    assert _clean_caption("what is this?") == "What is this?"
    assert _clean_caption("amazing!") == "Amazing!"


def test_clean_caption_strips_trailing_punctuation():
    assert _clean_caption("a dog...") == "A dog."
    assert _clean_caption("a cat,,,") == "A cat."


def test_clean_caption_handles_empty():
    assert _clean_caption("") == ""
    assert _clean_caption("   ") == ""


def test_weak_caption_filtering_disabled_accepts_short_captions(tmp_path):
    settings = Settings(
        service_name="test",
        database_url="sqlite:///:memory:",
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
        ml_device="cpu",
        ml_strict_cuda=False,
        ml_preload_models=False,
        media_worker_url="http://test",
        search_api_url="http://test",
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
        caption_enable_weak_filtering=False,
    )
    assert not _is_weak_caption(settings, "cat")
    assert not _is_weak_caption(settings, "a woman")
    assert not _is_weak_caption(settings, "an image")
