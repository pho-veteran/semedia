from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

SEMEDIA_ROOT = Path(__file__).resolve().parents[2]
SHARED_PATH = SEMEDIA_ROOT / "services" / "shared"

if str(SHARED_PATH) not in sys.path:
    sys.path.insert(0, str(SHARED_PATH))

from semedia_shared.database import build_engine, build_session_factory, init_database
from semedia_shared.models import MediaItem, ProcessingStatus, VideoScene

from .conftest import make_test_settings


SCRIPT_PATH = SEMEDIA_ROOT / "testing" / "reprocess_media.py"


def test_cli_runs_migrations_before_reprocessing(tmp_path, monkeypatch, capsys):
    """CLI runs pending migrations before starting reprocessing"""
    settings = make_test_settings("reprocess-cli", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    init_database(engine)

    # Add a media item so the script has something to reprocess
    with session_factory() as session:
        media = MediaItem(
            file_path="test.jpg",
            original_filename="test.jpg",
            media_type="image",
            status=ProcessingStatus.COMPLETED,
        )
        session.add(media)
        session.commit()

    calls = []

    def fake_get_settings(_service_name):
        return settings

    def fake_build_engine(_database_url):
        return engine

    def fake_build_session_factory(_engine):
        return session_factory

    def fake_run_pending_migrations(session, engine):
        calls.append("migrations")

    def fake_reprocess_media(settings_arg, session, media_ids):
        calls.append("reprocess")
        return {"total": len(media_ids), "succeeded": len(media_ids), "failed": 0, "failed_ids": []}

    monkeypatch.setattr("semedia_shared.config.get_settings", fake_get_settings)
    monkeypatch.setattr("semedia_shared.database.build_engine", fake_build_engine)
    monkeypatch.setattr("semedia_shared.database.build_session_factory", fake_build_session_factory)
    monkeypatch.setattr("semedia_shared.migrations.run_pending_migrations", fake_run_pending_migrations)
    monkeypatch.setattr("semedia_shared.reprocess.reprocess_media", fake_reprocess_media)

    monkeypatch.setattr(sys, "argv", ["reprocess_media.py"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(SCRIPT_PATH), run_name="__main__")

    assert exc_info.value.code == 0
    # init_database() calls run_pending_migrations once, then main() calls it again explicitly
    assert calls == ["migrations", "migrations", "reprocess"]

    engine.dispose()


def test_cli_filters_media_by_status(tmp_path, monkeypatch):
    """CLI selects media IDs matching the requested status filter"""
    settings = make_test_settings("reprocess-cli", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    init_database(engine)

    with session_factory() as session:
        completed = MediaItem(
            file_path="done.jpg",
            original_filename="done.jpg",
            media_type="image",
            status=ProcessingStatus.COMPLETED,
        )
        failed = MediaItem(
            file_path="failed.jpg",
            original_filename="failed.jpg",
            media_type="image",
            status=ProcessingStatus.FAILED,
        )
        session.add_all([completed, failed])
        session.commit()
        completed_id = completed.id

    captured = {}

    def fake_get_settings(_service_name):
        return settings

    def fake_build_engine(_database_url):
        return engine

    def fake_build_session_factory(_engine):
        return session_factory

    def fake_reprocess_media(settings_arg, session, media_ids):
        captured["media_ids"] = media_ids
        return {"total": len(media_ids), "succeeded": len(media_ids), "failed": 0, "failed_ids": []}

    monkeypatch.setattr("semedia_shared.config.get_settings", fake_get_settings)
    monkeypatch.setattr("semedia_shared.database.build_engine", fake_build_engine)
    monkeypatch.setattr("semedia_shared.database.build_session_factory", fake_build_session_factory)
    monkeypatch.setattr("semedia_shared.reprocess.reprocess_media", fake_reprocess_media)

    monkeypatch.setattr(sys, "argv", ["reprocess_media.py", "--status", "completed"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(SCRIPT_PATH), run_name="__main__")

    assert exc_info.value.code == 0
    assert captured["media_ids"] == [completed_id]

    engine.dispose()


def test_cli_uses_explicit_media_ids_when_provided(tmp_path, monkeypatch):
    """CLI uses --media-ids instead of status selection when explicitly provided"""
    settings = make_test_settings("reprocess-cli", tmp_path)

    captured = {}

    def fake_get_settings(_service_name):
        return settings

    def fake_reprocess_media(settings_arg, session, media_ids):
        captured["media_ids"] = media_ids
        return {"total": len(media_ids), "succeeded": len(media_ids), "failed": 0, "failed_ids": []}

    monkeypatch.setattr("semedia_shared.config.get_settings", fake_get_settings)
    monkeypatch.setattr("semedia_shared.reprocess.reprocess_media", fake_reprocess_media)

    monkeypatch.setattr(sys, "argv", ["reprocess_media.py", "--media-ids", "7", "8", "9"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(SCRIPT_PATH), run_name="__main__")

    assert exc_info.value.code == 0
    assert captured["media_ids"] == [7, 8, 9]


def test_cli_processes_in_batches(tmp_path, monkeypatch):
    """CLI splits selected media IDs into configured batch sizes"""
    settings = make_test_settings("reprocess-cli", tmp_path)

    batches = []

    def fake_get_settings(_service_name):
        return settings

    def fake_reprocess_media(settings_arg, session, media_ids):
        batches.append(media_ids)
        return {"total": len(media_ids), "succeeded": len(media_ids), "failed": 0, "failed_ids": []}

    monkeypatch.setattr("semedia_shared.config.get_settings", fake_get_settings)
    monkeypatch.setattr("semedia_shared.reprocess.reprocess_media", fake_reprocess_media)

    monkeypatch.setattr(
        sys,
        "argv",
        ["reprocess_media.py", "--media-ids", "1", "2", "3", "4", "5", "--batch-size", "2"],
    )

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(SCRIPT_PATH), run_name="__main__")

    assert exc_info.value.code == 0
    assert batches == [[1, 2], [3, 4], [5]]


def test_cli_reports_summary_statistics(tmp_path, monkeypatch, capsys):
    """CLI prints summary statistics after processing"""
    settings = make_test_settings("reprocess-cli", tmp_path)

    def fake_get_settings(_service_name):
        return settings

    def fake_reprocess_media(settings_arg, session, media_ids):
        return {"total": 3, "succeeded": 2, "failed": 1, "failed_ids": [3]}

    monkeypatch.setattr("semedia_shared.config.get_settings", fake_get_settings)
    monkeypatch.setattr("semedia_shared.reprocess.reprocess_media", fake_reprocess_media)

    monkeypatch.setattr(sys, "argv", ["reprocess_media.py", "--media-ids", "1", "2", "3"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
    output = capsys.readouterr().out

    assert exc_info.value.code == 1
    assert "Total media processed: 3" in output
    assert "Successful: 2" in output
    assert "Failed: 1" in output
    assert "Failed media IDs: 3" in output
