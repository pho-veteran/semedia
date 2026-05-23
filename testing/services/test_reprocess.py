from __future__ import annotations

from datetime import datetime, timedelta, timezone

from semedia_shared.models import MediaItem, ProcessingStatus
from semedia_shared.pipeline import process_media
from semedia_shared.reprocess import find_stuck_media, rebuild_keyword_index_repair, scan_storage_consistency

from .test_media_worker_pipeline import _prepare_session


def test_find_stuck_media_returns_old_pending_and_processing_items(tmp_path):
    settings, engine, session_factory = _prepare_session(tmp_path)
    now = datetime.now(timezone.utc)

    with session_factory() as session:
        session.add_all(
            [
                MediaItem(
                    file_path="originals/pending.jpg",
                    original_filename="pending.jpg",
                    media_type="image",
                    mime_type="image/jpeg",
                    file_size=1,
                    status=ProcessingStatus.PENDING,
                    enqueued_at=now - timedelta(hours=2),
                ),
                MediaItem(
                    file_path="originals/processing.jpg",
                    original_filename="processing.jpg",
                    media_type="image",
                    mime_type="image/jpeg",
                    file_size=1,
                    status=ProcessingStatus.PROCESSING,
                    enqueued_at=now - timedelta(hours=3),
                    updated_at=now - timedelta(hours=2),
                ),
            ]
        )
        session.commit()

        stuck = find_stuck_media(session, now=now, pending_after=timedelta(minutes=30), processing_after=timedelta(minutes=30))

    assert {item["status"] for item in stuck} == {ProcessingStatus.PENDING, ProcessingStatus.PROCESSING}
    engine.dispose()


def test_scan_storage_consistency_reports_orphans_and_missing_files(tmp_path):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    orphan_path = original_dir / "orphan.jpg"
    orphan_path.write_bytes(b"orphan")

    with session_factory() as session:
        session.add(
            MediaItem(
                file_path="originals/missing.jpg",
                original_filename="missing.jpg",
                media_type="image",
                mime_type="image/jpeg",
                file_size=1,
                status=ProcessingStatus.COMPLETED,
            )
        )
        session.commit()

        report = scan_storage_consistency(settings, session)

    assert "originals/orphan.jpg" in report["orphaned_original_files"]
    assert any(item["file_path"] == "originals/missing.jpg" for item in report["missing_media_files"])
    engine.dispose()


def test_rebuild_keyword_index_repair_rebuilds_current_artifact(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    (original_dir / "cat.jpg").write_bytes(b"image-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["cat on sofa"])
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [[0.1, 0.2, 0.3]])

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=11,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        assert process_media(settings, session, media.id) is True

        document_count = rebuild_keyword_index_repair(settings, session)

    assert document_count == 1
    engine.dispose()
