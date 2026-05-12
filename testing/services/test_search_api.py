from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from semedia_shared.models import MediaItem, ProcessingStatus, VideoScene
from semedia_shared.search_service import _normalize_scores

VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02\x00\x00\x00\x0bIDATx\xdac\xfc\xff"
    b"\x1f\x00\x03\x03\x02\x00\xef\xb2^*\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_search_health_endpoint(search_env):
    response = search_env["client"].get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "search-api"


def test_normalize_scores_clamps_without_min_max_inflation():
    results = [{"score": 0.02}, {"score": 0.6}, {"score": 1.2}, {"score": -0.5}]

    normalized = _normalize_scores(results)

    assert normalized == [
        {"score": 0.02},
        {"score": 0.6},
        {"score": 1.0},
        {"score": 0.0},
    ]



def test_search_text_prefers_strong_keyword_match_over_weak_vector_match(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        strong_keyword = MediaItem(
            file_path="originals/office.jpg",
            original_filename="office.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="office desk workspace laptop meeting room",
            embedding=[0.02, 0.0],
            index_key="media:1",
        )
        weak_keyword = MediaItem(
            file_path="originals/person.jpg",
            original_filename="person.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="a person standing outside",
            embedding=[0.6, 0.0],
            index_key="media:2",
        )
        session.add_all([strong_keyword, weak_keyword])
        session.commit()
        session.refresh(strong_keyword)
        session.refresh(weak_keyword)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "office desk", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["media_id"] == strong_keyword.id
    assert payload["results"][0]["caption"] == "office desk workspace laptop meeting room"
    assert payload["results"][1]["media_id"] == weak_keyword.id
    assert payload["results"][0]["score"] > payload["results"][1]["score"]



def test_search_text_deduplicates_duplicate_captions(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        relevant = MediaItem(
            file_path="originals/lake.jpg",
            original_filename="lake.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="moonlit lake water by a pier",
            embedding=[0.5, 0.0],
            index_key="media:1",
        )
        duplicate_one = MediaItem(
            file_path="originals/bat1.jpg",
            original_filename="bat1.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="there is a man that is standing in the dark with a bat",
            embedding=[0.55, 0.0],
            index_key="media:2",
        )
        duplicate_two = MediaItem(
            file_path="originals/bat2.jpg",
            original_filename="bat2.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="there is a man that is standing in the dark with a bat",
            embedding=[0.54, 0.0],
            index_key="media:3",
        )
        session.add_all([relevant, duplicate_one, duplicate_two])
        session.commit()
        session.refresh(relevant)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "water", "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    captions = [item["caption"] for item in payload["results"]]
    assert captions[0] == "moonlit lake water by a pier"
    assert captions.count("there is a man that is standing in the dark with a bat") == 1
    assert all(0.0 <= item["score"] <= 1.0 for item in payload["results"])


def test_search_text_limits_scenes_per_video(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        video = MediaItem(
            file_path="originals/film.mp4",
            original_filename="film.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:10",
        )
        other = MediaItem(
            file_path="originals/other.jpg",
            original_filename="other.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="different result",
            embedding=[0.5, 0.0],
            index_key="media:11",
        )
        session.add_all([video, other])
        session.commit()
        session.refresh(video)

        session.add_all(
            [
                VideoScene(
                    media_id=video.id,
                    scene_index=0,
                    start_time=0.0,
                    end_time=1.0,
                    caption="office desk workspace laptop meeting room",
                    embedding=[0.99, 0.0],
                    keyframe_path="keyframes/10/scene_0000.jpg",
                    thumbnail_path="thumbnails/10/scene_0000.jpg",
                    index_key="scene:10:0",
                ),
                VideoScene(
                    media_id=video.id,
                    scene_index=1,
                    start_time=1.0,
                    end_time=2.0,
                    caption="office desk workspace laptop meeting room two",
                    embedding=[0.98, 0.0],
                    keyframe_path="keyframes/10/scene_0001.jpg",
                    thumbnail_path="thumbnails/10/scene_0001.jpg",
                    index_key="scene:10:1",
                ),
                VideoScene(
                    media_id=video.id,
                    scene_index=2,
                    start_time=2.0,
                    end_time=3.0,
                    caption="office desk workspace laptop meeting room three",
                    embedding=[0.97, 0.0],
                    keyframe_path="keyframes/10/scene_0002.jpg",
                    thumbnail_path="thumbnails/10/scene_0002.jpg",
                    index_key="scene:10:2",
                ),
            ]
        )
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "office desk", "top_k": 10})

    assert response.status_code == 200
    payload = response.json()
    scene_results = [item for item in payload["results"] if item["media_id"] == video.id]
    assert len(scene_results) == 2
    assert scene_results[0]["scene_id"] != scene_results[1]["scene_id"]


def test_search_image_limits_scenes_per_video(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        video = MediaItem(
            file_path="originals/city.mp4",
            original_filename="city.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:20",
        )
        session.add(video)
        session.commit()
        session.refresh(video)

        session.add_all(
            [
                VideoScene(
                    media_id=video.id,
                    scene_index=0,
                    start_time=0.0,
                    end_time=1.0,
                    caption="blue city scene one",
                    embedding=[0.99, 0.0],
                    keyframe_path="keyframes/20/scene_0000.jpg",
                    thumbnail_path="thumbnails/20/scene_0000.jpg",
                    index_key="scene:20:0",
                ),
                VideoScene(
                    media_id=video.id,
                    scene_index=1,
                    start_time=1.0,
                    end_time=2.0,
                    caption="blue city scene two",
                    embedding=[0.98, 0.0],
                    keyframe_path="keyframes/20/scene_0001.jpg",
                    thumbnail_path="thumbnails/20/scene_0001.jpg",
                    index_key="scene:20:1",
                ),
                VideoScene(
                    media_id=video.id,
                    scene_index=2,
                    start_time=2.0,
                    end_time=3.0,
                    caption="blue city scene three",
                    embedding=[0.97, 0.0],
                    keyframe_path="keyframes/20/scene_0002.jpg",
                    thumbnail_path="thumbnails/20/scene_0002.jpg",
                    index_key="scene:20:2",
                ),
            ]
        )
        session.commit()

    monkeypatch.setattr(module, "_embed_image", lambda file: [1.0, 0.0])

    response = client.post(
        "/api/v1/search/by-image/",
        data={"top_k": "10"},
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    scene_results = [item for item in payload["results"] if item["media_id"] == video.id]
    assert len(scene_results) == 2
    assert all(0.0 <= item["score"] <= 1.0 for item in payload["results"])


def test_search_returns_normalized_scores(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="a cat on a sofa",
            embedding=[1.0, 0.0],
            index_key="media:30",
        )
        session.add(image)
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])
    monkeypatch.setattr(module, "_embed_image", lambda file: [1.0, 0.0])

    text_response = client.post("/api/v1/search/", json={"query_text": "cat", "top_k": 5})
    image_response = client.post(
        "/api/v1/search/by-image/",
        data={"top_k": "5"},
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert text_response.status_code == 200
    assert image_response.status_code == 200
    assert all(0.0 <= item["score"] <= 1.0 for item in text_response.json()["results"])
    assert all(0.0 <= item["score"] <= 1.0 for item in image_response.json()["results"])
    assert all(item["score"] <= 1.0 for item in text_response.json()["results"])
    assert all(item["score"] <= 1.0 for item in image_response.json()["results"])


def test_search_text_preserves_top_scene_for_video(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        video = MediaItem(
            file_path="originals/office.mp4",
            original_filename="office.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:40",
        )
        session.add(video)
        session.commit()
        session.refresh(video)

        top_scene = VideoScene(
            media_id=video.id,
            scene_index=0,
            start_time=0.0,
            end_time=1.0,
            caption="office desk workspace laptop meeting room",
            embedding=[0.99, 0.0],
            keyframe_path="keyframes/40/scene_0000.jpg",
            thumbnail_path="thumbnails/40/scene_0000.jpg",
            index_key="scene:40:0",
        )
        lower_scene = VideoScene(
            media_id=video.id,
            scene_index=1,
            start_time=1.0,
            end_time=2.0,
            caption="office room with chair",
            embedding=[0.8, 0.0],
            keyframe_path="keyframes/40/scene_0001.jpg",
            thumbnail_path="thumbnails/40/scene_0001.jpg",
            index_key="scene:40:1",
        )
        session.add_all([top_scene, lower_scene])
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "office desk", "top_k": 10})

    assert response.status_code == 200
    payload = response.json()
    video_results = [item for item in payload["results"] if item["media_id"] == video.id]
    assert video_results[0]["scene_id"] == top_scene.id
    assert video_results[0]["score"] >= video_results[1]["score"]


def test_search_text_exact_match_result_has_higher_score(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        exact_match = MediaItem(
            file_path="originals/exact.jpg",
            original_filename="exact.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="office desk workspace laptop",
            embedding=[0.6, 0.0],
            index_key="media:50",
        )
        loose_match = MediaItem(
            file_path="originals/loose.jpg",
            original_filename="loose.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="workspace with laptop and chair",
            embedding=[0.6, 0.0],
            index_key="media:51",
        )
        session.add_all([exact_match, loose_match])
        session.commit()
        session.refresh(exact_match)
        session.refresh(loose_match)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "office desk", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["media_id"] == exact_match.id
    assert payload["results"][0]["score"] > payload["results"][1]["score"]



def test_search_text_ignores_filename_only_match(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        filename_match = MediaItem(
            file_path="originals/irrelevant.jpg",
            original_filename="office-keyword.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="workspace scene alpha",
            embedding=[0.4, 0.0],
            index_key="media:80",
        )
        neutral = MediaItem(
            file_path="originals/neutral.jpg",
            original_filename="neutral.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="workspace scene beta",
            embedding=[0.4, 0.0],
            index_key="media:81",
        )
        session.add_all([filename_match, neutral])
        session.commit()
        session.refresh(filename_match)
        session.refresh(neutral)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "office", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    scores_by_id = {item["media_id"]: item["score"] for item in payload["results"]}
    assert scores_by_id[filename_match.id] == scores_by_id[neutral.id]



def test_search_results_are_sorted_by_descending_score(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        session.add_all(
            [
                MediaItem(
                    file_path="originals/high.jpg",
                    original_filename="high.jpg",
                    media_type="image",
                    mime_type="image/jpeg",
                    file_size=3,
                    status=ProcessingStatus.COMPLETED,
                    caption="cat on sofa",
                    embedding=[1.0, 0.0],
                    index_key="media:60",
                ),
                MediaItem(
                    file_path="originals/mid.jpg",
                    original_filename="mid.jpg",
                    media_type="image",
                    mime_type="image/jpeg",
                    file_size=3,
                    status=ProcessingStatus.COMPLETED,
                    caption="cat nearby",
                    embedding=[0.7, 0.0],
                    index_key="media:61",
                ),
                MediaItem(
                    file_path="originals/low.jpg",
                    original_filename="low.jpg",
                    media_type="image",
                    mime_type="image/jpeg",
                    file_size=3,
                    status=ProcessingStatus.COMPLETED,
                    caption="dog outside",
                    embedding=[0.3, 0.0],
                    index_key="media:62",
                ),
            ]
        )
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "cat", "top_k": 5})

    assert response.status_code == 200
    scores = [item["score"] for item in response.json()["results"]]
    assert scores == sorted(scores, reverse=True)



def test_search_respects_top_k_after_diversity(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        video = MediaItem(
            file_path="originals/series.mp4",
            original_filename="series.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:70",
        )
        other = MediaItem(
            file_path="originals/other.jpg",
            original_filename="other.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="office room",
            embedding=[0.8, 0.0],
            index_key="media:71",
        )
        session.add_all([video, other])
        session.commit()
        session.refresh(video)

        session.add_all(
            [
                VideoScene(
                    media_id=video.id,
                    scene_index=0,
                    start_time=0.0,
                    end_time=1.0,
                    caption="office desk one",
                    embedding=[0.99, 0.0],
                    keyframe_path="keyframes/70/scene_0000.jpg",
                    thumbnail_path="thumbnails/70/scene_0000.jpg",
                    index_key="scene:70:0",
                ),
                VideoScene(
                    media_id=video.id,
                    scene_index=1,
                    start_time=1.0,
                    end_time=2.0,
                    caption="office desk two",
                    embedding=[0.98, 0.0],
                    keyframe_path="keyframes/70/scene_0001.jpg",
                    thumbnail_path="thumbnails/70/scene_0001.jpg",
                    index_key="scene:70:1",
                ),
                VideoScene(
                    media_id=video.id,
                    scene_index=2,
                    start_time=2.0,
                    end_time=3.0,
                    caption="office desk three",
                    embedding=[0.97, 0.0],
                    keyframe_path="keyframes/70/scene_0002.jpg",
                    thumbnail_path="thumbnails/70/scene_0002.jpg",
                    index_key="scene:70:2",
                ),
            ]
        )
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "office desk", "top_k": 2})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) == 2
    assert all(0.0 <= item["score"] <= 1.0 for item in payload["results"])




def test_search_requires_query_text(search_env):
    response = search_env["client"].post("/api/v1/search/", json={"query_text": "   "})

    assert response.status_code == 422
    assert "query_text is required" in response.json()["detail"]


def test_search_requires_integer_top_k(search_env):
    response = search_env["client"].post("/api/v1/search/", json={"query_text": "cat", "top_k": "abc"})

    assert response.status_code == 422
    assert "top_k must be an integer" in response.json()["detail"]


def test_search_rejects_zero_top_k(search_env, monkeypatch):
    monkeypatch.setattr(search_env["module"], "_embed_text", lambda query_text: [1.0, 0.0])

    response = search_env["client"].post("/api/v1/search/", json={"query_text": "cat", "top_k": 0})

    assert response.status_code == 422
    assert response.json()["detail"] == "top_k must be greater than 0."


def test_search_rejects_negative_top_k(search_env, monkeypatch):
    monkeypatch.setattr(search_env["module"], "_embed_text", lambda query_text: [1.0, 0.0])

    response = search_env["client"].post("/api/v1/search/", json={"query_text": "cat", "top_k": -5})

    assert response.status_code == 422
    assert response.json()["detail"] == "top_k must be greater than 0."


def test_image_search_rejects_zero_top_k(search_env, monkeypatch):
    monkeypatch.setattr(search_env["module"], "_embed_image", lambda file: [1.0, 0.0])

    response = search_env["client"].post(
        "/api/v1/search/by-image/",
        data={"top_k": "0"},
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "top_k must be greater than 0."


def test_image_search_rejects_negative_top_k(search_env, monkeypatch):
    monkeypatch.setattr(search_env["module"], "_embed_image", lambda file: [1.0, 0.0])

    response = search_env["client"].post(
        "/api/v1/search/by-image/",
        data={"top_k": "-5"},
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "top_k must be greater than 0."


def test_search_returns_ranked_results(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="a cat on a sofa",
            embedding=[1.0, 0.0],
            index_key="media:1",
        )
        video = MediaItem(
            file_path="originals/dog.mp4",
            original_filename="dog.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:2",
        )
        session.add_all([image, video])
        session.commit()
        session.refresh(image)
        session.refresh(video)

        session.add(
            VideoScene(
                media_id=video.id,
                scene_index=0,
                start_time=1.0,
                end_time=3.0,
                caption="a dog running in a park",
                embedding=[0.7, 0.3],
                keyframe_path="keyframes/2/scene_0000.jpg",
                thumbnail_path="thumbnails/2/scene_0000.jpg",
                index_key="scene:2:0",
            )
        )
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "cat on sofa", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["results"][0]["media_id"] == image.id
    assert payload["results"][0]["result_type"] == "image"
    assert payload["query_mode"] == "text"


def test_image_search_returns_ranked_results(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/red.jpg",
            original_filename="red.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="a red square",
            embedding=[1.0, 0.0],
            index_key="media:1",
        )
        video = MediaItem(
            file_path="originals/city.mp4",
            original_filename="city.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:2",
        )
        session.add_all([image, video])
        session.commit()
        session.refresh(image)
        session.refresh(video)

        session.add(
            VideoScene(
                media_id=video.id,
                scene_index=0,
                start_time=5.0,
                end_time=8.0,
                caption="a busy blue city scene",
                embedding=[0.4, 0.6],
                keyframe_path="keyframes/2/scene_0000.jpg",
                thumbnail_path="thumbnails/2/scene_0000.jpg",
                index_key="scene:2:0",
            )
        )
        session.commit()

    monkeypatch.setattr(module, "_embed_image", lambda file: [1.0, 0.0])

    response = client.post(
        "/api/v1/search/by-image/",
        data={"top_k": "5"},
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query_mode"] == "image"
    assert payload["query_image_name"] == "query.png"
    assert payload["count"] >= 1
    assert payload["results"][0]["media_id"] == image.id
    assert payload["results"][0]["result_type"] == "image"


def test_video_scene_results_use_stable_scene_keys(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        video = MediaItem(
            file_path="originals/city.mp4",
            original_filename="duplicate-name.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:1",
        )
        session.add(video)
        session.commit()
        session.refresh(video)

        scene = VideoScene(
            media_id=video.id,
            scene_index=0,
            start_time=0.0,
            end_time=1.0,
            caption="blue city scene",
            embedding=[1.0, 0.0],
            keyframe_path="keyframes/1/scene_0000.jpg",
            thumbnail_path="thumbnails/1/scene_0000.jpg",
            index_key="scene:1:0",
        )
        session.add(scene)
        session.commit()
        session.refresh(scene)
        scene_id = scene.id

    monkeypatch.setattr(module, "_embed_image", lambda file: [1.0, 0.0])

    response = client.post(
        "/api/v1/search/by-image/",
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["scene_key"] == f"scene:{video.original_filename}:{scene.scene_index}"


def test_search_returns_service_unavailable_when_worker_embedding_fails(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]

    def raise_unavailable(query_text: str):
        raise module.HTTPException(status_code=503, detail="Media worker unavailable: boom")

    monkeypatch.setattr(module, "_embed_text", raise_unavailable)

    response = client.post("/api/v1/search/", json={"query_text": "cat"})

    assert response.status_code == 503
    assert "Media worker unavailable" in response.json()["detail"]


def test_image_search_returns_service_unavailable_when_worker_embedding_fails(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]

    def raise_unavailable(file):
        raise module.HTTPException(status_code=503, detail="Media worker unavailable: boom")

    monkeypatch.setattr(module, "_embed_image", raise_unavailable)

    response = client.post(
        "/api/v1/search/by-image/",
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 503
    assert "Media worker unavailable" in response.json()["detail"]


def test_search_logs_when_worker_embedding_request_fails(search_env, monkeypatch, caplog):
    module = search_env["module"]
    client = search_env["client"]

    monkeypatch.setattr(
        module.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("worker boom")),
    )

    with caplog.at_level(logging.ERROR):
        response = client.post("/api/v1/search/", json={"query_text": "cat"})

    assert response.status_code == 503
    assert "Media worker unavailable" in response.json()["detail"]
    assert "Text embedding request failed." in caplog.text


def test_image_search_rejects_non_images(search_env):
    response = search_env["client"].post(
        "/api/v1/search/by-image/",
        files={"file": ("query.txt", b"not-an-image", "text/plain")},
    )

    assert response.status_code == 422
    assert "Unsupported media type" in response.json()["detail"]


def test_keyword_search_uses_media_caption_for_ranking(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="red sofa living room sunlight",
            index_key="media:1",
        )
        session.add(image)
        session.commit()
        session.refresh(image)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [0.5, 0.5])

    response = client.post("/api/v1/search/", json={"query_text": "sunlight sofa", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["media_id"] == image.id
    assert payload["results"][0]["caption"] == "red sofa living room sunlight"



def test_keyword_search_uses_scene_caption_for_ranking(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        video = MediaItem(
            file_path="originals/dog.mp4",
            original_filename="dog.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:2",
        )
        session.add(video)
        session.commit()
        session.refresh(video)

        scene = VideoScene(
            media_id=video.id,
            scene_index=0,
            start_time=1.0,
            end_time=3.0,
            caption="sunny day park trees grass",
            keyframe_path="keyframes/2/scene_0000.jpg",
            thumbnail_path="thumbnails/2/scene_0000.jpg",
            index_key="scene:2:0",
        )
        session.add(scene)
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [0.5, 0.5])

    response = client.post("/api/v1/search/", json={"query_text": "park trees", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["result_type"] == "video_scene"
    assert payload["results"][0]["scene_id"] == scene.id
    assert payload["results"][0]["caption"] == "sunny day park trees grass"



def test_keyword_search_uses_caption_when_available(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="a cat on a sofa",
            index_key="media:1",
        )
        session.add(image)
        session.commit()
        session.refresh(image)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [0.5, 0.5])

    response = client.post("/api/v1/search/", json={"query_text": "cat sofa", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["media_id"] == image.id
    assert payload["results"][0]["caption"] == "a cat on a sofa"


def test_search_database_creates_keyword_index_artifact_table(search_env):
    engine = search_env["module"].engine

    assert inspect(engine).has_table("keyword_index_artifacts")


def test_keyword_search_builds_index_artifact_when_missing(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="red sofa living room sunlight",
            index_key="media:1",
        )
        session.add(image)
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [0.5, 0.5])

    response = client.post("/api/v1/search/", json={"query_text": "sunlight sofa", "top_k": 5})

    assert response.status_code == 200

    with session_factory() as session:
        assert session.execute(text("SELECT COUNT(*) FROM keyword_index_artifacts")).scalar_one() == 1


def test_keyword_search_is_stable_across_repeated_queries(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="red sofa living room sunlight",
            index_key="media:1",
        )
        session.add(image)
        session.commit()
        session.refresh(image)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [0.5, 0.5])

    first = client.post("/api/v1/search/", json={"query_text": "sunlight sofa", "top_k": 5})
    second = client.post("/api/v1/search/", json={"query_text": "sunlight sofa", "top_k": 5})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["results"] == second.json()["results"]


def test_keyword_search_returns_empty_when_no_captions_exist(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/blank.jpg",
            original_filename="blank.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:1",
        )
        session.add(image)
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [0.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "sunlight sofa", "top_k": 5})

    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_keyword_search_refreshes_when_artifact_timestamp_changes(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="red sofa living room sunlight",
            index_key="media:1",
        )
        session.add(image)
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [0.5, 0.5])

    first = client.post("/api/v1/search/", json={"query_text": "sunlight sofa", "top_k": 5})
    assert first.status_code == 200

    with session_factory() as session:
        session.execute(text("UPDATE keyword_index_artifacts SET updated_at = CURRENT_TIMESTAMP"))
        session.commit()

    second = client.post("/api/v1/search/", json={"query_text": "sunlight sofa", "top_k": 5})

    assert second.status_code == 200
    assert second.json()["results"] == first.json()["results"]


def test_search_text_returns_component_scores_and_explanation(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/office.jpg",
            original_filename="office.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="office desk",
            embedding=[0.3, 0.9539392014],
            index_key="media:90",
        )
        session.add(image)
        session.commit()
        session.refresh(image)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "office desk", "top_k": 5})

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["media_id"] == image.id
    assert result["vector_score"] == 0.3
    assert result["keyword_score"] == 1.0
    assert result["explanation"] == {
        "match_type": "caption",
        "exact_phrase_match": True,
        "rich_caption": False,
        "rerank_boost": 0.08,
    }


def test_image_search_returns_visual_explanation(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/red.jpg",
            original_filename="red.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="a red square",
            embedding=[1.0, 0.0],
            index_key="media:91",
        )
        session.add(image)
        session.commit()
        session.refresh(image)

    monkeypatch.setattr(module, "_embed_image", lambda file: [1.0, 0.0])

    response = client.post(
        "/api/v1/search/by-image/",
        data={"top_k": "5"},
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["media_id"] == image.id
    assert result["vector_score"] == 1.0
    assert result["keyword_score"] == 0.0
    assert result["explanation"] == {
        "match_type": "visual",
        "exact_phrase_match": False,
        "rich_caption": False,
        "rerank_boost": 0.0,
    }


def test_search_keyword_exact_top_k(search_env, monkeypatch):
    """Verify that search_keyword() returns exactly top_k results, not top_k * 2."""
    module = search_env["module"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        # Create 10 media items with distinct captions
        for i in range(10):
            image = MediaItem(
                file_path=f"originals/item_{i}.jpg",
                original_filename=f"item_{i}.jpg",
                media_type="image",
                mime_type="image/jpeg",
                file_size=3,
                status=ProcessingStatus.COMPLETED,
                caption=f"office desk workspace item {i}",
                index_key=f"media:{100+i}",
            )
            session.add(image)
        session.commit()

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [0.5, 0.5])

    # Rebuild the keyword index to include all items
    from semedia_shared.index_service import rebuild_keyword_index
    with session_factory() as session:
        rebuild_keyword_index(module.settings, session)

    # Call search_keyword directly with top_k=3
    from semedia_shared.index_service import search_keyword, ensure_keyword_index_current
    with session_factory() as session:
        index_data = ensure_keyword_index_current(module.settings, session)
        results = search_keyword("office desk", index_data, top_k=3)

    # Should return exactly 3 results, not 6 (3 * 2)
    assert len(results) == 3, f"Expected exactly 3 results, got {len(results)}"


