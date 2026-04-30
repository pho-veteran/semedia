from __future__ import annotations

from pathlib import Path

import pytest

from semedia_shared.config import Settings
from semedia_shared.database import build_engine, build_session_factory, init_database
from semedia_shared.models import MediaItem, MediaType, ProcessingStatus, VideoScene
from semedia_shared.serialization import scene_payload
from semedia_shared.storage import delete_media_files, ensure_media_root


@pytest.fixture
def test_settings(tmp_path):
    settings = Settings(
        service_name="test-serialization",
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
        ml_device="cpu",
        ml_strict_cuda=False,
        ml_preload_models=False,
        media_worker_url="http://media-worker.test",
        search_api_url="http://search-api.test",
        allow_all_origins=True,
    )
    ensure_media_root(settings)
    return settings


@pytest.fixture
def db_session(test_settings):
    engine = build_engine(test_settings.database_url)
    session_factory = build_session_factory(engine)
    init_database(engine)

    session = session_factory()
    yield session
    session.close()
    engine.dispose()


def test_scene_payload_uses_best_frame_index_for_caption(test_settings, db_session):
    """scene_payload should use captions[best_frame_index] when available"""
    media = MediaItem(
        file_path="videos/test.mp4",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
        file_size=1000,
        status=ProcessingStatus.COMPLETED,
    )
    db_session.add(media)
    db_session.flush()

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        caption="legacy caption",
        captions=["frame 0 caption", "frame 1 caption", "frame 2 caption"],
        best_frame_index=1,
    )
    db_session.add(scene)
    db_session.commit()

    payload = scene_payload(test_settings, scene)

    assert payload["caption"] == "frame 1 caption"


def test_scene_payload_uses_best_frame_index_for_thumbnail(test_settings, db_session):
    """scene_payload should use thumbnail_paths[best_frame_index] when available"""
    media = MediaItem(
        file_path="videos/test.mp4",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
        file_size=1000,
        status=ProcessingStatus.COMPLETED,
    )
    db_session.add(media)
    db_session.flush()

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        thumbnail_path="thumbnails/legacy.jpg",
        thumbnail_paths=["thumbnails/frame_0.jpg", "thumbnails/frame_1.jpg", "thumbnails/frame_2.jpg"],
        best_frame_index=2,
    )
    db_session.add(scene)
    db_session.commit()

    payload = scene_payload(test_settings, scene)

    assert payload["thumbnail_image"] == "/media/thumbnails/frame_2.jpg"


def test_scene_payload_falls_back_to_legacy_caption_when_array_missing(test_settings, db_session):
    """scene_payload should fall back to singular caption when captions array is None"""
    media = MediaItem(
        file_path="videos/test.mp4",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
        file_size=1000,
        status=ProcessingStatus.COMPLETED,
    )
    db_session.add(media)
    db_session.flush()

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        caption="legacy caption",
        captions=None,
        best_frame_index=0,
    )
    db_session.add(scene)
    db_session.commit()

    payload = scene_payload(test_settings, scene)

    assert payload["caption"] == "legacy caption"


def test_scene_payload_falls_back_when_best_frame_index_out_of_range(test_settings, db_session):
    """scene_payload should fall back to singular fields when best_frame_index is out of range"""
    media = MediaItem(
        file_path="videos/test.mp4",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
        file_size=1000,
        status=ProcessingStatus.COMPLETED,
    )
    db_session.add(media)
    db_session.flush()

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        caption="legacy caption",
        thumbnail_path="thumbnails/legacy.jpg",
        captions=["frame 0 caption"],
        thumbnail_paths=["thumbnails/frame_0.jpg"],
        best_frame_index=5,  # Out of range
    )
    db_session.add(scene)
    db_session.commit()

    payload = scene_payload(test_settings, scene)

    assert payload["caption"] == "legacy caption"
    assert payload["thumbnail_image"] == "/media/thumbnails/legacy.jpg"


def test_scene_payload_falls_back_when_selected_value_empty(test_settings, db_session):
    """scene_payload should fall back to singular fields when array value is empty string"""
    media = MediaItem(
        file_path="videos/test.mp4",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
        file_size=1000,
        status=ProcessingStatus.COMPLETED,
    )
    db_session.add(media)
    db_session.flush()

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        caption="legacy caption",
        thumbnail_path="thumbnails/legacy.jpg",
        captions=["", "frame 1 caption"],
        thumbnail_paths=["", "thumbnails/frame_1.jpg"],
        best_frame_index=0,  # Points to empty string
    )
    db_session.add(scene)
    db_session.commit()

    payload = scene_payload(test_settings, scene)

    assert payload["caption"] == "legacy caption"
    assert payload["thumbnail_image"] == "/media/thumbnails/legacy.jpg"


def test_delete_media_files_removes_all_keyframe_paths(test_settings, db_session):
    """delete_media_files should delete all files in keyframe_paths array"""
    media = MediaItem(
        file_path="videos/test.mp4",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
        file_size=1000,
        status=ProcessingStatus.COMPLETED,
    )
    db_session.add(media)
    db_session.flush()

    # Create actual files
    keyframe_0 = test_settings.media_root / "keyframes" / "frame_0.jpg"
    keyframe_1 = test_settings.media_root / "keyframes" / "frame_1.jpg"
    keyframe_2 = test_settings.media_root / "keyframes" / "frame_2.jpg"
    keyframe_0.parent.mkdir(parents=True, exist_ok=True)
    keyframe_0.write_text("frame0")
    keyframe_1.write_text("frame1")
    keyframe_2.write_text("frame2")

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        keyframe_path="keyframes/frame_0.jpg",  # Legacy field
        keyframe_paths=["keyframes/frame_0.jpg", "keyframes/frame_1.jpg", "keyframes/frame_2.jpg"],
    )
    db_session.add(scene)
    db_session.commit()

    delete_media_files(test_settings, media)

    assert not keyframe_0.exists()
    assert not keyframe_1.exists()
    assert not keyframe_2.exists()


def test_delete_media_files_removes_all_thumbnail_paths(test_settings, db_session):
    """delete_media_files should delete all files in thumbnail_paths array"""
    media = MediaItem(
        file_path="videos/test.mp4",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
        file_size=1000,
        status=ProcessingStatus.COMPLETED,
    )
    db_session.add(media)
    db_session.flush()

    # Create actual files
    thumb_0 = test_settings.media_root / "thumbnails" / "thumb_0.jpg"
    thumb_1 = test_settings.media_root / "thumbnails" / "thumb_1.jpg"
    thumb_0.parent.mkdir(parents=True, exist_ok=True)
    thumb_0.write_text("thumb0")
    thumb_1.write_text("thumb1")

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        thumbnail_path="thumbnails/thumb_0.jpg",  # Legacy field
        thumbnail_paths=["thumbnails/thumb_0.jpg", "thumbnails/thumb_1.jpg"],
    )
    db_session.add(scene)
    db_session.commit()

    delete_media_files(test_settings, media)

    assert not thumb_0.exists()
    assert not thumb_1.exists()


def test_delete_media_files_falls_back_to_legacy_paths_when_arrays_missing(test_settings, db_session):
    """delete_media_files should fall back to singular paths when arrays are None"""
    media = MediaItem(
        file_path="videos/test.mp4",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
        file_size=1000,
        status=ProcessingStatus.COMPLETED,
    )
    db_session.add(media)
    db_session.flush()

    # Create actual files
    keyframe = test_settings.media_root / "keyframes" / "legacy.jpg"
    thumbnail = test_settings.media_root / "thumbnails" / "legacy.jpg"
    keyframe.parent.mkdir(parents=True, exist_ok=True)
    thumbnail.parent.mkdir(parents=True, exist_ok=True)
    keyframe.write_text("keyframe")
    thumbnail.write_text("thumbnail")

    scene = VideoScene(
        media_id=media.id,
        scene_index=0,
        start_time=0.0,
        end_time=5.0,
        keyframe_path="keyframes/legacy.jpg",
        thumbnail_path="thumbnails/legacy.jpg",
        keyframe_paths=None,
        thumbnail_paths=None,
    )
    db_session.add(scene)
    db_session.commit()

    delete_media_files(test_settings, media)

    assert not keyframe.exists()
    assert not thumbnail.exists()
