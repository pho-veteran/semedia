from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import inspect, text

from semedia_shared.database import build_engine, build_session_factory, init_database
from semedia_shared.models import MediaItem, ProcessingStatus, VideoScene
from semedia_shared.pipeline import process_media
from semedia_shared.storage import ensure_media_root
from semedia_shared.video_service import SceneSpan

from .conftest import make_test_settings


def _prepare_session(tmp_path: Path):
    settings = make_test_settings("media-worker", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    ensure_media_root(settings)
    init_database(engine)
    return settings, engine, session_factory


def test_process_media_image_populates_caption_and_embedding(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    image_path = original_dir / "sample.jpg"
    image_path.write_bytes(b"image-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["test caption"])
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [[0.1, 0.2, 0.3]])

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/sample.jpg",
            original_filename="sample.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=11,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        media_id = media.id

        assert process_media(settings, session, media_id) is True

        session.refresh(media)
        assert media.status == ProcessingStatus.COMPLETED
        assert media.caption == "test caption"
        assert media.embedding == [0.1, 0.2, 0.3]
        assert media.index_key == f"media:{media_id}"
        assert media.processed_at is not None

    engine.dispose()


def test_process_media_video_uses_single_frame_extraction(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    video_path = original_dir / "sample.mp4"
    video_path.write_bytes(b"video-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "get_video_duration", lambda path: 2.0)
    monkeypatch.setattr(
        pipeline_module,
        "detect_scenes",
        lambda settings, path: [
            SceneSpan(scene_index=0, start_time=0.0, end_time=1.0),
            SceneSpan(scene_index=1, start_time=1.0, end_time=2.0),
        ],
    )

    def fake_extract_single(settings, path, media_id, scene):
        keyframe_dir = settings.media_root / "keyframes" / str(media_id)
        thumbnail_dir = settings.media_root / "thumbnails" / str(media_id)
        keyframe_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)

        keyframe = keyframe_dir / f"scene_{scene.scene_index:04d}.jpg"
        thumbnail = thumbnail_dir / f"scene_{scene.scene_index:04d}.jpg"
        keyframe.write_bytes(f"keyframe-{scene.scene_index}".encode())
        thumbnail.write_bytes(f"thumbnail-{scene.scene_index}".encode())

        return str(keyframe), str(thumbnail)

    monkeypatch.setattr(pipeline_module, "extract_scene_keyframe", fake_extract_single)
    monkeypatch.setattr(
        pipeline_module,
        "generate_captions",
        lambda settings, paths: ["scene 0 caption", "scene 1 caption"]
    )
    monkeypatch.setattr(
        pipeline_module,
        "encode_images",
        lambda settings, paths: [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
    )

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/sample.mp4",
            original_filename="sample.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=11,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        media_id = media.id

        assert process_media(settings, session, media_id) is True

        session.refresh(media)
        scenes = session.query(VideoScene).filter(VideoScene.media_id == media_id).order_by(VideoScene.scene_index).all()

        assert media.status == ProcessingStatus.COMPLETED
        assert media.duration == 2.0
        assert len(scenes) == 2

        scene0 = scenes[0]
        assert scene0.keyframe_path == f"keyframes/{media_id}/scene_0000.jpg"
        assert scene0.thumbnail_path == f"thumbnails/{media_id}/scene_0000.jpg"
        assert scene0.caption == "scene 0 caption"
        assert scene0.embedding == [1.0, 0.0, 0.0]
        assert scene0.index_key == f"scene:{media_id}:0"

        scene1 = scenes[1]
        assert scene1.caption == "scene 1 caption"
        assert scene1.embedding == [0.0, 1.0, 0.0]
        assert scene1.index_key == f"scene:{media_id}:1"

        assert media.caption == "scene 0 caption scene 1 caption"
        assert media.index_key == f"media:{media_id}"

    engine.dispose()


def test_process_media_marks_item_failed_when_pipeline_errors(tmp_path, monkeypatch, caplog):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    image_path = original_dir / "broken.jpg"
    image_path.write_bytes(b"image-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(
        pipeline_module,
        "generate_captions",
        lambda settings, paths: (_ for _ in ()).throw(RuntimeError("caption failure")),
    )
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [[0.1, 0.2, 0.3]])

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/broken.jpg",
            original_filename="broken.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=11,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        media_id = media.id

        with caplog.at_level(logging.ERROR):
            assert process_media(settings, session, media_id) is False

        session.refresh(media)
        assert media.status == ProcessingStatus.FAILED
        assert "caption failure" in media.error_message

    assert "Processing failed for media" in caplog.text

    engine.dispose()


def test_process_media_creates_keyword_index_artifact_table(tmp_path):
    settings, engine, session_factory = _prepare_session(tmp_path)

    assert inspect(engine).has_table("keyword_index_artifacts")

    engine.dispose()


def test_process_media_rebuilds_keyword_index_artifact(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    image_path = original_dir / "sample.jpg"
    image_path.write_bytes(b"image-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["test caption"])
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [[0.1, 0.2, 0.3]])

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/sample.jpg",
            original_filename="sample.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=11,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)

        assert process_media(settings, session, media.id) is True
        assert session.execute(text("SELECT COUNT(*) FROM keyword_index_artifacts")).scalar_one() == 1

    engine.dispose()
