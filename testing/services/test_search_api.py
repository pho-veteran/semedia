from __future__ import annotations

import logging

from semedia_shared.models import MediaItem, ProcessingStatus, VideoScene

VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02\x00\x00\x00\x0bIDATx\xdac\xfc\xff"
    b"\x1f\x00\x03\x03\x02\x00\xef\xb2^*\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_search_health_endpoint(search_env):
    response = search_env["client"].get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "search-api"


def test_search_requires_query_text(search_env):
    response = search_env["client"].post("/api/v1/search/", json={"query_text": "   "})

    assert response.status_code == 422
    assert "query_text is required" in response.json()["detail"]


def test_search_requires_integer_top_k(search_env):
    response = search_env["client"].post("/api/v1/search/", json={"query_text": "cat", "top_k": "abc"})

    assert response.status_code == 422
    assert "top_k must be an integer" in response.json()["detail"]


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
