from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from semedia_shared.models import MediaItem, ProcessingStatus

from .conftest import load_service_module, make_test_settings

VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02\x00\x00\x00\x0bIDATx\xdac\xfc\xff"
    b"\x1f\x00\x03\x03\x02\x00\xef\xb2^*\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_worker_runtime_endpoint_reports_cpu_configuration(worker_env):
    response = worker_env["client"].get("/internal/runtime")

    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_device"] == "cpu"
    assert payload["strict_cuda"] is False
    assert payload["preload_models"] is False


def test_worker_embed_text_requires_text(worker_env):
    response = worker_env["client"].post("/internal/embeddings/text", json={"text": "   "})

    assert response.status_code == 422
    assert "text is required" in response.json()["detail"]


def test_worker_embed_image_returns_embedding(worker_env, monkeypatch):
    module = worker_env["module"]

    monkeypatch.setattr(module, "encode_images", lambda settings, paths: [[0.1, 0.2, 0.3]])

    response = worker_env["client"].post(
        "/internal/embeddings/image",
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {"embedding": [0.1, 0.2, 0.3]}


def test_worker_embed_image_rejects_non_images(worker_env):
    response = worker_env["client"].post(
        "/internal/embeddings/image",
        files={"file": ("query.txt", b"not-an-image", "text/plain")},
    )

    assert response.status_code == 422
    assert "Unsupported media type" in response.json()["detail"]


def test_worker_process_endpoint_invokes_pipeline(worker_env, monkeypatch):
    module = worker_env["module"]
    client = worker_env["client"]
    session_factory = worker_env["session_factory"]

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

    calls: list[tuple[str, int]] = []

    def fake_process(settings, session, incoming_media_id: int) -> bool:
        media = session.get(MediaItem, incoming_media_id)
        media.status = ProcessingStatus.COMPLETED
        session.commit()
        calls.append((settings.service_name, incoming_media_id))
        return True

    monkeypatch.setattr(module, "process_media", fake_process)

    response = client.post(f"/internal/media/{media_id}/process")

    assert response.status_code == 200
    assert response.json() == {"media_id": media_id, "success": True}
    assert calls == [("media-worker", media_id)]

    with session_factory() as session:
        media = session.get(MediaItem, media_id)
        assert media is not None
        assert media.status == ProcessingStatus.COMPLETED


def test_worker_startup_preloads_models_when_enabled(tmp_path, monkeypatch):
    module = load_service_module("media_worker_service_main_preload", "services/media_worker/app/main.py")
    settings = replace(make_test_settings("media-worker", tmp_path), ml_preload_models=True)

    monkeypatch.setattr(module, "settings", settings)
    monkeypatch.setattr(module, "init_database", lambda _engine: None)
    calls: list[str] = []
    monkeypatch.setattr(module, "warm_models", lambda incoming_settings: calls.append(incoming_settings.service_name))

    with TestClient(module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert calls == ["media-worker"]
