from __future__ import annotations

import sys
from pathlib import Path

import pytest

SEMEDIA_ROOT = Path(__file__).resolve().parents[2]
SHARED_PATH = SEMEDIA_ROOT / "services" / "shared"

if str(SHARED_PATH) not in sys.path:
    sys.path.insert(0, str(SHARED_PATH))

from semedia_shared.database import build_engine, build_session_factory, init_database
from semedia_shared.models import MediaItem, ProcessingStatus, VideoScene
from semedia_shared.reprocess import reprocess_media
from semedia_shared.storage import ensure_media_root

from .conftest import make_test_settings


def test_reprocess_media_calls_process_media_for_each_id(tmp_path, monkeypatch):
    """reprocess_media calls process_media for each media_id in the list"""
    settings = make_test_settings("reprocess-test", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    ensure_media_root(settings)
    init_database(engine)

    session = session_factory()

    media1 = MediaItem(
        file_path="test1.jpg",
        original_filename="test1.jpg",
        media_type="image",
        status=ProcessingStatus.COMPLETED,
    )
    media2 = MediaItem(
        file_path="test2.jpg",
        original_filename="test2.jpg",
        media_type="image",
        status=ProcessingStatus.COMPLETED,
    )
    session.add_all([media1, media2])
    session.commit()
    media_ids = [media1.id, media2.id]
    session.close()

    processed_ids = []

    def fake_process_media(settings, session, media_id):
        processed_ids.append(media_id)
        return True

    from semedia_shared import reprocess as reprocess_module

    monkeypatch.setattr(reprocess_module, "process_media", fake_process_media)

    session = session_factory()
    result = reprocess_media(settings, session, media_ids)
    session.close()

    assert processed_ids == media_ids
    assert result["total"] == 2
    assert result["succeeded"] == 2
    assert result["failed"] == 0

    engine.dispose()


def test_reprocess_media_handles_processing_failures(tmp_path, monkeypatch):
    """reprocess_media tracks failures and continues processing remaining items"""
    settings = make_test_settings("reprocess-test", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    ensure_media_root(settings)
    init_database(engine)

    session = session_factory()

    media1 = MediaItem(
        file_path="test1.jpg",
        original_filename="test1.jpg",
        media_type="image",
        status=ProcessingStatus.COMPLETED,
    )
    media2 = MediaItem(
        file_path="test2.jpg",
        original_filename="test2.jpg",
        media_type="image",
        status=ProcessingStatus.COMPLETED,
    )
    media3 = MediaItem(
        file_path="test3.jpg",
        original_filename="test3.jpg",
        media_type="image",
        status=ProcessingStatus.COMPLETED,
    )
    session.add_all([media1, media2, media3])
    session.commit()
    media_ids = [media1.id, media2.id, media3.id]
    session.close()

    def fake_process_media(settings, session, media_id):
        if media_id == media_ids[1]:
            return False
        return True

    from semedia_shared import reprocess as reprocess_module

    monkeypatch.setattr(reprocess_module, "process_media", fake_process_media)

    session = session_factory()
    result = reprocess_media(settings, session, media_ids)
    session.close()

    assert result["total"] == 3
    assert result["succeeded"] == 2
    assert result["failed"] == 1
    assert media_ids[1] in result["failed_ids"]

    engine.dispose()


def test_reprocess_media_logs_progress(tmp_path, monkeypatch, caplog):
    """reprocess_media logs progress for each media item"""
    import logging

    settings = make_test_settings("reprocess-test", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    ensure_media_root(settings)
    init_database(engine)

    session = session_factory()

    media1 = MediaItem(
        file_path="test1.jpg",
        original_filename="test1.jpg",
        media_type="image",
        status=ProcessingStatus.COMPLETED,
    )
    session.add(media1)
    session.commit()
    media_id = media1.id
    session.close()

    def fake_process_media(settings, session, media_id):
        return True

    from semedia_shared import reprocess as reprocess_module

    monkeypatch.setattr(reprocess_module, "process_media", fake_process_media)

    session = session_factory()
    with caplog.at_level(logging.INFO):
        reprocess_media(settings, session, [media_id])
    session.close()

    assert f"Reprocessing media {media_id}" in caplog.text
    assert "Reprocessing complete" in caplog.text

    engine.dispose()


def test_reprocess_media_is_idempotent(tmp_path, monkeypatch):
    """reprocess_media can be run multiple times on the same media without issues"""
    settings = make_test_settings("reprocess-test", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    ensure_media_root(settings)
    init_database(engine)

    session = session_factory()

    media1 = MediaItem(
        file_path="test1.jpg",
        original_filename="test1.jpg",
        media_type="image",
        status=ProcessingStatus.COMPLETED,
    )
    session.add(media1)
    session.commit()
    media_id = media1.id
    session.close()

    call_count = 0

    def fake_process_media(settings, session, media_id):
        nonlocal call_count
        call_count += 1
        return True

    from semedia_shared import reprocess as reprocess_module

    monkeypatch.setattr(reprocess_module, "process_media", fake_process_media)

    session = session_factory()
    result1 = reprocess_media(settings, session, [media_id])
    session.close()

    session = session_factory()
    result2 = reprocess_media(settings, session, [media_id])
    session.close()

    assert call_count == 2
    assert result1["succeeded"] == 1
    assert result2["succeeded"] == 1

    engine.dispose()


def test_reprocess_media_populates_phase2_fields_for_existing_video(tmp_path, monkeypatch):
    """reprocess_media regenerates scene frames and Phase 2 fields for existing videos"""
    settings = make_test_settings("reprocess-test", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    ensure_media_root(settings)
    init_database(engine)

    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    video_path = original_dir / "legacy.mp4"
    video_path.write_bytes(b"legacy-video")

    from semedia_shared import pipeline as pipeline_module
    from semedia_shared.video_service import SceneSpan

    monkeypatch.setattr(pipeline_module, "get_video_duration", lambda path: 3.0)
    monkeypatch.setattr(
        pipeline_module,
        "detect_scenes",
        lambda settings, path: [SceneSpan(scene_index=0, start_time=0.0, end_time=3.0)],
    )

    def fake_extract_multi(settings, path, media_id, scene):
        keyframe_dir = settings.media_root / "keyframes" / str(media_id)
        thumbnail_dir = settings.media_root / "thumbnails" / str(media_id)
        keyframe_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        keyframe_paths = []
        thumbnail_paths = []
        for frame_idx in range(3):
            keyframe = keyframe_dir / f"scene_{scene.scene_index:04d}_frame_{frame_idx:02d}.jpg"
            thumbnail = thumbnail_dir / f"scene_{scene.scene_index:04d}_frame_{frame_idx:02d}.jpg"
            keyframe.write_bytes(f"keyframe-{frame_idx}".encode())
            thumbnail.write_bytes(f"thumbnail-{frame_idx}".encode())
            keyframe_paths.append(str(keyframe))
            thumbnail_paths.append(str(thumbnail))
        return keyframe_paths, thumbnail_paths

    monkeypatch.setattr(pipeline_module, "extract_scene_keyframes", fake_extract_multi)
    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["f0", "f1", "f2"])
    monkeypatch.setattr(
        pipeline_module,
        "encode_images",
        lambda settings, paths: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/legacy.mp4",
            original_filename="legacy.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=12,
            status=ProcessingStatus.COMPLETED,
            caption="old caption",
        )
        session.add(media)
        session.flush()
        session.add(
            VideoScene(
                media_id=media.id,
                scene_index=0,
                start_time=0.0,
                end_time=3.0,
                keyframe_path="old.jpg",
                thumbnail_path="old-thumb.jpg",
                caption="old scene caption",
                embedding=[0.2, 0.3, 0.4],
            )
        )
        session.commit()
        media_id = media.id

    with session_factory() as session:
        result = reprocess_media(settings, session, [media_id])
        assert result["succeeded"] == 1

    with session_factory() as session:
        media = session.get(MediaItem, media_id)
        scenes = session.query(VideoScene).filter(VideoScene.media_id == media_id).all()
        assert media.retrieval_text == "f0 f1 f2"
        assert media.caption == "f1"
        assert len(scenes) == 1
        assert scenes[0].best_frame_index == 1
        assert len(scenes[0].keyframe_paths) == 3
        assert len(scenes[0].thumbnail_paths) == 3
        assert len(scenes[0].captions) == 3
        assert len(scenes[0].embeddings) == 3

    engine.dispose()
