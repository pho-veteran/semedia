from __future__ import annotations

import logging
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from semedia_shared.models import MediaItem, ProcessingStatus, VideoScene

VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02\x00\x00\x00\x0bIDATx\xdac\xfc\xff"
    b"\x1f\x00\x03\x03\x02\x00\xef\xb2^*\x00\x00\x00\x00IEND\xaeB`\x82"
)


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload

    @property
    def text(self) -> str:
        return str(self._payload)


def test_gateway_health_endpoint(gateway_env):
    response = gateway_env["client"].get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json()["service"] == "gateway-api"


def test_gateway_runtime_proxies_worker_status(gateway_env, monkeypatch):
    module = gateway_env["module"]
    client = gateway_env["client"]

    monkeypatch.setattr(
        module.requests,
        "get",
        lambda url, timeout: _FakeResponse(
            {
                "requested_device": "cuda",
                "strict_cuda": True,
                "selected_device": "cuda",
            }
        ),
    )

    response = client.get("/api/v1/runtime/")

    assert response.status_code == 200
    assert response.json()["selected_device"] == "cuda"


def test_upload_media_creates_record_and_dispatches_worker(gateway_env, monkeypatch):
    module = gateway_env["module"]
    client = gateway_env["client"]
    session_factory = gateway_env["session_factory"]

    dispatched_ids: list[int] = []
    monkeypatch.setattr(module, "_trigger_worker_processing", lambda media_id: dispatched_ids.append(media_id))

    response = client.post(
        "/api/v1/media/upload/",
        files={"file": ("sample.jpg", b"image-bytes", "image/jpeg")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["processing_enqueued"] is True
    assert payload["data"]["media_type"] == "image"
    assert payload["data"]["status"] == ProcessingStatus.PENDING

    with session_factory() as session:
        media_items = session.query(MediaItem).all()
        assert len(media_items) == 1
        media = media_items[0]
        assert media.original_filename == "sample.jpg"
        assert media.status == ProcessingStatus.PENDING
        assert media.file_size == len(b"image-bytes")

    assert dispatched_ids == [media.id]


def test_upload_media_rejects_unsupported_media_type(gateway_env):
    client = TestClient(gateway_env["module"].app, raise_server_exceptions=False)

    response = client.post(
        "/api/v1/media/upload/",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422
    assert "Unsupported media type" in response.json()["detail"]


def test_upload_media_cleans_saved_file_when_persist_fails(gateway_env, monkeypatch):
    module = gateway_env["module"]
    settings = gateway_env["settings"]
    client = TestClient(module.app, raise_server_exceptions=False)

    saved_path = settings.media_root / "originals" / "2026" / "05" / "04" / "broken.jpg"
    saved_path.parent.mkdir(parents=True, exist_ok=True)

    def fake_save_upload(settings, upload_file):
        saved_path.write_bytes(b"image-bytes")
        return "originals/2026/05/04/broken.jpg", len(b"image-bytes")

    monkeypatch.setattr(module, "save_upload", fake_save_upload)
    monkeypatch.setattr(
        module,
        "_persist_uploaded_media",
        lambda session, media: (_ for _ in ()).throw(RuntimeError("db write failed")),
        raising=False,
    )

    response = client.post(
        "/api/v1/media/upload/",
        files={"file": ("broken.jpg", b"image-bytes", "image/jpeg")},
    )

    assert response.status_code == 500
    assert not saved_path.exists()


def test_delete_media_removes_database_rows_and_files(gateway_env):
    client = gateway_env["client"]
    settings = gateway_env["settings"]
    session_factory = gateway_env["session_factory"]

    media_path = settings.media_root / "originals" / "2026" / "04" / "14"
    scene_path = settings.media_root / "keyframes" / "7"
    thumb_path = settings.media_root / "thumbnails" / "7"
    media_path.mkdir(parents=True, exist_ok=True)
    scene_path.mkdir(parents=True, exist_ok=True)
    thumb_path.mkdir(parents=True, exist_ok=True)

    media_file = media_path / "sample.mp4"
    keyframe_file = scene_path / "scene_0000.jpg"
    thumbnail_file = thumb_path / "scene_0000.jpg"
    media_file.write_bytes(b"video")
    keyframe_file.write_bytes(b"frame")
    thumbnail_file.write_bytes(b"thumb")

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/2026/04/14/sample.mp4",
            original_filename="sample.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=5,
            status=ProcessingStatus.COMPLETED,
            index_key="media:7",
        )
        session.add(media)
        session.commit()
        session.refresh(media)

        session.add(
            VideoScene(
                media_id=media.id,
                scene_index=0,
                start_time=0.0,
                end_time=1.0,
                keyframe_path="keyframes/7/scene_0000.jpg",
                thumbnail_path="thumbnails/7/scene_0000.jpg",
                caption="frame",
                index_key="scene:7:0",
            )
        )
        session.commit()
        media_id = media.id

    response = client.delete(f"/api/v1/media/{media_id}/")

    assert response.status_code == 204
    assert not media_file.exists()
    assert not keyframe_file.exists()
    assert not thumbnail_file.exists()

    with session_factory() as session:
        assert session.query(MediaItem).count() == 0
        assert session.query(VideoScene).count() == 0


def test_delete_media_rebuilds_keyword_index_artifact(gateway_env):
    client = gateway_env["client"]
    settings = gateway_env["settings"]
    session_factory = gateway_env["session_factory"]

    media_path = settings.media_root / "originals" / "2026" / "04" / "14"
    scene_path = settings.media_root / "keyframes" / "7"
    thumb_path = settings.media_root / "thumbnails" / "7"
    media_path.mkdir(parents=True, exist_ok=True)
    scene_path.mkdir(parents=True, exist_ok=True)
    thumb_path.mkdir(parents=True, exist_ok=True)

    media_file = media_path / "sample.mp4"
    keyframe_file = scene_path / "scene_0000.jpg"
    thumbnail_file = thumb_path / "scene_0000.jpg"
    media_file.write_bytes(b"video")
    keyframe_file.write_bytes(b"frame")
    thumbnail_file.write_bytes(b"thumb")

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/2026/04/14/sample.mp4",
            original_filename="sample.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=5,
            status=ProcessingStatus.COMPLETED,
            caption="sample caption",
            index_key="media:7",
        )
        session.add(media)
        session.commit()
        session.refresh(media)

        session.add(
            VideoScene(
                media_id=media.id,
                scene_index=0,
                start_time=0.0,
                end_time=1.0,
                keyframe_path="keyframes/7/scene_0000.jpg",
                thumbnail_path="thumbnails/7/scene_0000.jpg",
                caption="frame",
                index_key="scene:7:0",
            )
        )
        session.commit()
        session.execute(text("CREATE TABLE IF NOT EXISTS keyword_index_artifacts (id INTEGER PRIMARY KEY, artifact_key VARCHAR(64), format_version VARCHAR(16), document_count INTEGER, payload BLOB, built_at DATETIME, updated_at DATETIME)"))
        session.execute(text("INSERT INTO keyword_index_artifacts (artifact_key, format_version, document_count, payload) VALUES ('default', 'v1', 2, x'00')"))
        session.commit()
        media_id = media.id

    response = client.delete(f"/api/v1/media/{media_id}/")

    assert response.status_code == 204

    with session_factory() as session:
        assert session.execute(text("SELECT COUNT(*) FROM keyword_index_artifacts")).scalar_one() == 1
        assert session.execute(text("SELECT document_count FROM keyword_index_artifacts WHERE artifact_key = 'default'")) .scalar_one() == 0


def test_delete_media_preserves_files_when_db_delete_fails(gateway_env, monkeypatch):
    module = gateway_env["module"]
    settings = gateway_env["settings"]
    session_factory = gateway_env["session_factory"]
    client = TestClient(module.app, raise_server_exceptions=False)

    media_dir = settings.media_root / "originals" / "2026" / "05" / "04"
    media_dir.mkdir(parents=True, exist_ok=True)
    media_file = media_dir / "sample.mp4"
    media_file.write_bytes(b"video")

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/2026/05/04/sample.mp4",
            original_filename="sample.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=5,
            status=ProcessingStatus.COMPLETED,
            index_key="media:1",
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        media_id = media.id

    monkeypatch.setattr(
        module,
        "_delete_media_row",
        lambda session, media: (_ for _ in ()).throw(RuntimeError("db delete failed")),
        raising=False,
    )

    response = client.delete(f"/api/v1/media/{media_id}/")

    assert response.status_code == 500
    assert media_file.exists()


def test_gateway_search_proxies_search_api(gateway_env, monkeypatch):
    module = gateway_env["module"]
    client = gateway_env["client"]

    def fake_post(url, json, timeout):
        assert url.endswith("/api/v1/search/")
        assert json == {"query_text": "cat", "top_k": 3}
        return _FakeResponse(
            {
                "query_text": "cat",
                "count": 1,
                "results": [{"media_id": 9, "result_type": "image", "score": 0.88}],
            }
        )

    monkeypatch.setattr(module.requests, "post", fake_post)

    response = client.post("/api/v1/search/", json={"query_text": "cat", "top_k": 3})

    assert response.status_code == 200
    assert response.json()["results"][0]["media_id"] == 9


def test_gateway_image_search_proxies_search_api(gateway_env, monkeypatch):
    module = gateway_env["module"]
    client = gateway_env["client"]

    def fake_post(url, files, data, timeout):
        assert url.endswith("/api/v1/search/by-image/")
        assert files["file"][0] == "query.png"
        assert data == {"top_k": "4"}
        return _FakeResponse(
            {
                "query_mode": "image",
                "query_image_name": "query.png",
                "count": 1,
                "results": [{"media_id": 12, "result_type": "image", "score": 1.0}],
            }
        )

    monkeypatch.setattr(module.requests, "post", fake_post)

    response = client.post(
        "/api/v1/search/by-image/",
        data={"top_k": "4"},
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["query_mode"] == "image"
    assert response.json()["results"][0]["media_id"] == 12


def test_worker_dispatch_failure_is_logged_and_marks_media_failed(gateway_env, monkeypatch, caplog):
    module = gateway_env["module"]
    session_factory = gateway_env["session_factory"]

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/2026/04/14/sample.jpg",
            original_filename="sample.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        media_id = media.id

    monkeypatch.setattr(
        module.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("worker is down")),
    )

    with caplog.at_level(logging.ERROR):
        module._trigger_worker_processing(media_id)

    with session_factory() as session:
        media = session.get(MediaItem, media_id)
        assert media is not None
        assert media.status == ProcessingStatus.FAILED
        assert "worker is down" in media.error_message

    assert "Worker dispatch failed for media" in caplog.text
