from __future__ import annotations

import logging
from pathlib import Path

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


def test_process_media_image_populates_retrieval_text(tmp_path, monkeypatch):
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
        assert media.retrieval_text == "test caption"
        assert media.embedding == [0.1, 0.2, 0.3]
        assert media.index_key == f"media:{media_id}"
        assert media.processed_at is not None

    engine.dispose()


def test_process_media_video_uses_multi_frame_extraction_and_aggregation(tmp_path, monkeypatch):
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
            keyframe.write_bytes(f"keyframe-{scene.scene_index}-{frame_idx}".encode())
            thumbnail.write_bytes(f"thumbnail-{scene.scene_index}-{frame_idx}".encode())
            keyframe_paths.append(str(keyframe))
            thumbnail_paths.append(str(thumbnail))

        return keyframe_paths, thumbnail_paths

    monkeypatch.setattr(pipeline_module, "extract_scene_keyframes", fake_extract_multi)

    # 2 scenes * 3 frames = 6 captions and embeddings
    monkeypatch.setattr(
        pipeline_module,
        "generate_captions",
        lambda settings, paths: ["s0f0", "s0f1", "s0f2", "s1f0", "s1f1", "s1f2"]
    )
    monkeypatch.setattr(
        pipeline_module,
        "encode_images",
        lambda settings, paths: [
            [1.0, 0.0, 0.0],  # s0f0
            [0.0, 1.0, 0.0],  # s0f1
            [0.0, 0.0, 1.0],  # s0f2
            [0.5, 0.5, 0.0],  # s1f0
            [0.5, 0.0, 0.5],  # s1f1
            [0.0, 0.5, 0.5],  # s1f2
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

        # Scene 0 checks
        scene0 = scenes[0]
        assert scene0.keyframe_paths == [
            f"keyframes/{media_id}/scene_0000_frame_00.jpg",
            f"keyframes/{media_id}/scene_0000_frame_01.jpg",
            f"keyframes/{media_id}/scene_0000_frame_02.jpg",
        ]
        assert scene0.thumbnail_paths == [
            f"thumbnails/{media_id}/scene_0000_frame_00.jpg",
            f"thumbnails/{media_id}/scene_0000_frame_01.jpg",
            f"thumbnails/{media_id}/scene_0000_frame_02.jpg",
        ]
        assert scene0.captions == ["s0f0", "s0f1", "s0f2"]
        assert scene0.embeddings == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        assert scene0.best_frame_index == 1

        # Singular fields derived from best_frame_index
        assert scene0.caption == "s0f1"
        assert scene0.keyframe_path == f"keyframes/{media_id}/scene_0000_frame_01.jpg"
        assert scene0.thumbnail_path == f"thumbnails/{media_id}/scene_0000_frame_01.jpg"

        # Embedding should be normalized mean of 3 embeddings
        import math
        expected_mean = [1.0/3, 1.0/3, 1.0/3]
        norm = math.sqrt(sum(x**2 for x in expected_mean))
        expected_normalized = [x/norm for x in expected_mean]
        assert len(scene0.embedding) == 3
        for i in range(3):
            assert abs(scene0.embedding[i] - expected_normalized[i]) < 0.001

        # retrieval_text should be unique captions joined
        assert scene0.retrieval_text == "s0f0 s0f1 s0f2"
        assert scene0.index_key == f"scene:{media_id}:0"

        # Scene 1 checks
        scene1 = scenes[1]
        assert scene1.captions == ["s1f0", "s1f1", "s1f2"]
        assert scene1.best_frame_index == 1
        assert scene1.caption == "s1f1"
        assert scene1.retrieval_text == "s1f0 s1f1 s1f2"

        # Media-level aggregation
        assert media.caption == "s0f1 s1f1"  # First 3 distinct scene captions (only 2 scenes)
        assert media.retrieval_text == "s0f0 s0f1 s0f2 s1f0 s1f1 s1f2"  # First 10 scene retrieval_texts
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
