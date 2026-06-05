from __future__ import annotations

import json
from pathlib import Path

from semedia_shared.evaluation_seed import SeedEvaluationLock
from semedia_shared.models import MediaItem, ProcessingStatus


def _write_eval_corpus(evaluation_dir: Path, filenames: list[str]) -> None:
    assets_dir = evaluation_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, filename in enumerate(filenames, start=1):
        (assets_dir / filename).write_bytes(b"asset-bytes")
        manifest.append({"asset_id": f"asset-{index}", "filename": filename})
    (evaluation_dir / "asset_manifest.json").write_text(json.dumps(manifest))


def test_seed_media_returns_summary(gateway_env, monkeypatch, tmp_path):
    module = gateway_env["module"]
    client = gateway_env["client"]
    session_factory = gateway_env["session_factory"]
    evaluation_dir = tmp_path / "evaluation"
    _write_eval_corpus(evaluation_dir, ["one.jpg", "two.jpg"])

    monkeypatch.setattr(module.evaluation_module, "EVAL_DIR", evaluation_dir)
    monkeypatch.setattr(
        module.evaluation_module,
        "seed_evaluation_media",
        lambda evaluation_dir, base_url, session: {
            "message": "Evaluation media seeding finished.",
            "total": 2,
            "uploaded": 2,
            "completed": 2,
            "failed": 0,
            "skipped": 0,
            "elapsed_seconds": 1.23,
            "results": [
                {"asset_id": "asset-1", "filename": "one.jpg", "status": "completed", "media_id": 1, "caption": "one", "skipped": False, "detail": None},
                {"asset_id": "asset-2", "filename": "two.jpg", "status": "completed", "media_id": 2, "caption": "two", "skipped": False, "detail": None},
            ],
        },
    )

    response = client.post("/api/v1/evaluation/seed-media")

    assert response.status_code == 200
    payload = response.json()
    assert payload["uploaded"] == 2
    assert payload["completed"] == 2
    assert payload["failed"] == 0
    assert len(payload["results"]) == 2


def test_seed_media_rejects_concurrent_runs(gateway_env, monkeypatch):
    module = gateway_env["module"]
    client = gateway_env["client"]
    lock = SeedEvaluationLock()
    assert lock.acquire() is True
    monkeypatch.setattr(module.evaluation_module, "_SEED_LOCK", lock)

    response = client.post("/api/v1/evaluation/seed-media")

    assert response.status_code == 409
    assert response.json()["detail"] == "Evaluation media seeding is already running."


def test_seed_media_returns_not_found_when_manifest_missing(gateway_env, monkeypatch, tmp_path):
    module = gateway_env["module"]
    client = gateway_env["client"]
    monkeypatch.setattr(module.evaluation_module, "EVAL_DIR", tmp_path / "missing-evaluation")

    response = client.post("/api/v1/evaluation/seed-media")

    assert response.status_code == 404
    assert "Asset manifest not found" in response.json()["detail"]


def test_seed_media_skips_already_seeded_files(gateway_env, tmp_path, monkeypatch):
    from semedia_shared.evaluation_seed import seed_evaluation_media

    session_factory = gateway_env["session_factory"]
    evaluation_dir = tmp_path / "evaluation"
    _write_eval_corpus(evaluation_dir, ["seeded.jpg"])

    with session_factory() as session:
        session.add(
            MediaItem(
                file_path="originals/2026/06/04/seeded.jpg",
                original_filename="seeded.jpg",
                media_type="image",
                mime_type="image/jpeg",
                file_size=10,
                status=ProcessingStatus.COMPLETED,
                caption="already there",
                index_key="media:1",
            )
        )
        session.commit()

        upload_called = False

        def fake_upload(base_url, file_path):
            nonlocal upload_called
            upload_called = True
            return {"data": {"id": 999}}

        monkeypatch.setattr("semedia_shared.evaluation_seed.upload_file", fake_upload)

        summary = seed_evaluation_media(
            evaluation_dir=evaluation_dir,
            base_url="http://example.test",
            session=session,
        )

    assert upload_called is False
    assert summary["skipped"] == 1
    assert summary["uploaded"] == 0
    assert summary["results"][0]["filename"] == "seeded.jpg"
    assert summary["results"][0]["skipped"] is True
