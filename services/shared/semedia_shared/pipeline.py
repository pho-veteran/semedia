from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .caption_service import generate_captions
from .clip_service import encode_images
from .log import get_logger
from .models import MediaItem, ProcessingStatus, VideoScene
from .storage import relative_to_media_root
from .video_service import detect_scenes, extract_scene_keyframe, get_video_duration

logger = get_logger(__name__)


def process_media(settings, session: Session, media_id: int) -> bool:
    media = session.execute(
        select(MediaItem).options(selectinload(MediaItem.scenes)).where(MediaItem.id == media_id)
    ).scalar_one()
    logger.info("Processing started for media %s (%s).", media_id, media.media_type)
    media.status = ProcessingStatus.PROCESSING
    media.error_message = ""
    media.updated_at = datetime.now(timezone.utc)
    session.commit()

    try:
        if media.is_image:
            _process_image(settings, session, media)
        else:
            _process_video(settings, session, media)
    except Exception as exc:
        logger.exception("Processing failed for media %s", media_id)
        media.status = ProcessingStatus.FAILED
        media.error_message = str(exc)
        media.updated_at = datetime.now(timezone.utc)
        session.commit()
        return False

    media.status = ProcessingStatus.COMPLETED
    media.processed_at = datetime.now(timezone.utc)
    media.updated_at = datetime.now(timezone.utc)
    session.commit()

    try:
        from .index_service import rebuild_keyword_index

        session.expire_all()
        rebuild_keyword_index(settings, session)
    except Exception:
        logger.exception("Keyword index rebuild failed for media %s", media_id)

    logger.info("Processing completed for media %s.", media_id)
    return True


def _process_image(settings, session: Session, media: MediaItem) -> None:
    path = str(settings.media_root / media.file_path)
    captions = generate_captions(settings, [path])
    embeddings = encode_images(settings, [path])
    media.caption = captions[0] if captions else ""
    media.embedding = embeddings[0] if embeddings else None
    media.index_key = f"media:{media.id}"
    media.updated_at = datetime.now(timezone.utc)
    session.commit()


def _process_video(settings, session: Session, media: MediaItem) -> None:
    video_path = str(settings.media_root / media.file_path)
    media.duration = get_video_duration(video_path)
    media.updated_at = datetime.now(timezone.utc)
    session.commit()

    scenes = detect_scenes(settings, video_path)
    if not scenes:
        raise ValueError("No scenes detected and video duration could not be determined.")

    for scene in list(media.scenes):
        session.delete(scene)
    session.commit()

    frame_paths: list[str] = []
    scene_payloads: list[dict] = []
    for scene in scenes:
        keyframe_path, thumbnail_path = extract_scene_keyframe(settings, video_path, media.id, scene)
        frame_paths.append(keyframe_path)
        scene_payloads.append(
            {
                "scene_index": scene.scene_index,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "keyframe_path": keyframe_path,
                "thumbnail_path": thumbnail_path,
            }
        )

    captions = generate_captions(settings, frame_paths)
    for i in range(1, len(captions)):
        if captions[i] and captions[i] == captions[i - 1]:
            logger.warning("Adjacent scenes %d and %d have identical captions: %s", i - 1, i, captions[i])
            captions[i] = f"{captions[i]} (scene {i + 1})"

    embeddings = encode_images(settings, frame_paths)

    created_scenes: list[VideoScene] = []
    for payload, caption, embedding in zip(scene_payloads, captions, embeddings):
        created_scenes.append(
            VideoScene(
                media_id=media.id,
                scene_index=payload["scene_index"],
                start_time=payload["start_time"],
                end_time=payload["end_time"],
                keyframe_path=relative_to_media_root(settings, payload["keyframe_path"]),
                thumbnail_path=relative_to_media_root(settings, payload["thumbnail_path"]),
                caption=caption,
                embedding=embedding,
                index_key=f"scene:{media.id}:{payload['scene_index']}",
            )
        )

    session.add_all(created_scenes)
    media.caption = _truncate_text(_join_unique_non_empty([scene.caption for scene in created_scenes], max_items=3), 200)
    media.index_key = f"media:{media.id}"
    media.updated_at = datetime.now(timezone.utc)
    session.commit()


def _join_unique_non_empty(values: list[str], max_items: int | None = None) -> str:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique_values.append(cleaned)
        if max_items is not None and len(unique_values) >= max_items:
            break
    return " ".join(unique_values)


def _truncate_text(value: str, max_length: int) -> str:
    return value[:max_length].rstrip()
