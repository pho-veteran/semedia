from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import inspect, text

from semedia_shared.database import build_engine, build_session_factory, init_database
from semedia_shared.index_service import load_keyword_index, search_keyword
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


def test_process_media_returns_false_when_media_row_is_missing(tmp_path, caplog):
    settings, engine, session_factory = _prepare_session(tmp_path)

    with session_factory() as session:
        with caplog.at_level(logging.WARNING):
            assert process_media(settings, session, 999) is False

    assert "Media 999 no longer exists" in caplog.text
    engine.dispose()


def test_process_media_generates_quality_captions(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    image_path = original_dir / "sample.jpg"
    image_path.write_bytes(b"image-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["A golden retriever running in a park."])
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

        session.refresh(media)
        assert media.status == ProcessingStatus.COMPLETED
        assert media.caption
        assert len(media.caption.split()) > 2
        assert "an image" not in media.caption.lower()
        assert media.caption[-1] in ".!?"

    engine.dispose()


def test_process_media_replaces_generic_caption_after_retry(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    image_path = original_dir / "sample.jpg"
    image_path.write_bytes(b"image-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["Image content unclear."])
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

        session.refresh(media)
        assert media.status == ProcessingStatus.COMPLETED
        assert media.caption == "Image content unclear."
        assert "a close up of a" not in media.caption.lower()
        assert "there is a" not in media.caption.lower()

    engine.dispose()



def test_process_video_flags_duplicate_adjacent_captions(tmp_path, monkeypatch, caplog):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    video_path = original_dir / "sample.mp4"
    video_path.write_bytes(b"video-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "get_video_duration", lambda path: 3.0)
    monkeypatch.setattr(
        pipeline_module,
        "detect_scenes",
        lambda settings, path: [
            SceneSpan(scene_index=0, start_time=0.0, end_time=1.0),
            SceneSpan(scene_index=1, start_time=1.0, end_time=2.0),
            SceneSpan(scene_index=2, start_time=2.0, end_time=3.0),
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
        lambda settings, paths: ["A person walking.", "A person walking.", "A person sitting."],
    )
    monkeypatch.setattr(
        pipeline_module,
        "encode_images",
        lambda settings, paths: [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
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

        with caplog.at_level(logging.WARNING):
            assert process_media(settings, session, media_id) is True

        session.refresh(media)
        scenes = session.query(VideoScene).filter(VideoScene.media_id == media_id).order_by(VideoScene.scene_index).all()

        assert media.status == ProcessingStatus.COMPLETED
        assert len(scenes) == 3
        assert scenes[0].caption == "A person walking."
        assert scenes[1].caption == "A person walking. (scene 2)"
        assert scenes[2].caption == "A person sitting."

    assert "Adjacent scenes 0 and 1 have identical captions" in caplog.text

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



def test_process_media_video_rebuilds_keyword_index_with_new_scenes(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    video_path = original_dir / "dog.mp4"
    video_path.write_bytes(b"video-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "get_video_duration", lambda path: 3.0)
    monkeypatch.setattr(
        pipeline_module,
        "detect_scenes",
        lambda settings, path: [
            SceneSpan(scene_index=0, start_time=0.0, end_time=1.0),
            SceneSpan(scene_index=1, start_time=1.0, end_time=2.0),
            SceneSpan(scene_index=2, start_time=2.0, end_time=3.0),
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
        lambda settings, paths: [
            "There is a dog sitting on the floor.",
            "There is a dog laying down on the floor.",
            "There is a dog laying on the floor with its mouth open.",
        ],
    )
    monkeypatch.setattr(
        pipeline_module,
        "encode_images",
        lambda settings, paths: [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
    )

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/dog.mp4",
            original_filename="dog.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=11,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)

        assert process_media(settings, session, media.id) is True

        index_data = load_keyword_index(session)
        assert index_data is not None
        assert index_data.document_count == 3

        dog_results = search_keyword("dog", index_data, 10)
        assert {item["scene_id"] for item in dog_results} == {1, 2, 3}
        assert all(item["original_filename"] == "dog.mp4" for item in dog_results)
        assert all(item["score"] > 0 for item in dog_results)

    engine.dispose()


def test_process_media_video_preserves_existing_scenes_when_caption_count_is_short(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    (original_dir / "sample.mp4").write_bytes(b"video-bytes")

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
        keyframe.write_bytes(b"frame")
        thumbnail.write_bytes(b"thumb")
        return str(keyframe), str(thumbnail)

    monkeypatch.setattr(pipeline_module, "extract_scene_keyframe", fake_extract_single)
    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["only one caption"])
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [[1.0, 0.0], [0.0, 1.0]])

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/sample.mp4",
            original_filename="sample.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=11,
            status=ProcessingStatus.COMPLETED,
            caption="old summary",
            index_key="media:1",
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
                caption="old scene",
                embedding=[0.5, 0.5],
                keyframe_path=f"keyframes/{media.id}/scene_0000.jpg",
                thumbnail_path=f"thumbnails/{media.id}/scene_0000.jpg",
                index_key=f"scene:{media.id}:0",
            )
        )
        session.commit()

        assert process_media(settings, session, media.id) is False
        session.refresh(media)
        scenes = session.query(VideoScene).filter(VideoScene.media_id == media.id).order_by(VideoScene.scene_index).all()

        assert media.status == ProcessingStatus.FAILED
        assert "Expected 2 captions, got 1" in media.error_message
        assert len(scenes) == 1
        assert scenes[0].caption == "old scene"

    engine.dispose()


def test_process_media_video_cleans_generated_files_when_replacement_fails(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    (original_dir / "sample.mp4").write_bytes(b"video-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "get_video_duration", lambda path: 2.0)
    monkeypatch.setattr(
        pipeline_module,
        "detect_scenes",
        lambda settings, path: [SceneSpan(scene_index=0, start_time=0.0, end_time=2.0)],
    )

    def fake_extract_single(settings, path, media_id, scene):
        keyframe_dir = settings.media_root / "keyframes" / str(media_id)
        thumbnail_dir = settings.media_root / "thumbnails" / str(media_id)
        keyframe_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        keyframe = keyframe_dir / "scene_0000.jpg"
        thumbnail = thumbnail_dir / "scene_0000.jpg"
        keyframe.write_bytes(b"frame")
        thumbnail.write_bytes(b"thumb")
        return str(keyframe), str(thumbnail)

    monkeypatch.setattr(pipeline_module, "extract_scene_keyframe", fake_extract_single)
    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["caption"])
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [])

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

        assert process_media(settings, session, media_id) is False

    assert not (settings.media_root / f"keyframes/{media_id}/scene_0000.jpg").exists()
    assert not (settings.media_root / f"thumbnails/{media_id}/scene_0000.jpg").exists()
    engine.dispose()
