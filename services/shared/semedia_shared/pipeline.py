from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .caption_service import generate_captions
from .clip_service import encode_images
from .log import get_logger
from .models import MediaItem, ProcessingStatus, VideoScene
from .storage import relative_to_media_root
from .video_service import detect_scenes, extract_scene_keyframe, extract_scene_keyframes, get_video_duration

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
    logger.info("Processing completed for media %s.", media_id)
    return True


def _process_image(settings, session: Session, media: MediaItem) -> None:
    path = str(settings.media_root / media.file_path)
    captions = generate_captions(settings, [path])
    embeddings = encode_images(settings, [path])
    media.caption = captions[0] if captions else ""
    media.retrieval_text = media.caption
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

    all_frame_paths: list[str] = []
    scene_payloads: list[dict] = []
    for scene in scenes:
        keyframe_paths, thumbnail_paths = extract_scene_keyframes(
            settings,
            video_path,
            media.id,
            scene,
        )
        all_frame_paths.extend(keyframe_paths)
        scene_payloads.append(
            {
                "scene_index": scene.scene_index,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "keyframe_paths": keyframe_paths,
                "thumbnail_paths": thumbnail_paths,
            }
        )

    captions = generate_captions(settings, all_frame_paths)
    embeddings = encode_images(settings, all_frame_paths)

    created_scenes: list[VideoScene] = []
    for scene_offset, payload in enumerate(scene_payloads):
        frame_start = scene_offset * 3
        frame_end = frame_start + 3
        scene_captions = captions[frame_start:frame_end]
        scene_embeddings = embeddings[frame_start:frame_end]
        best_frame_index = 1
        relative_keyframe_paths = [relative_to_media_root(settings, path) for path in payload["keyframe_paths"]]
        relative_thumbnail_paths = [relative_to_media_root(settings, path) for path in payload["thumbnail_paths"]]
        retrieval_text = _join_unique_non_empty(scene_captions)

        created_scenes.append(
            VideoScene(
                media_id=media.id,
                scene_index=payload["scene_index"],
                start_time=payload["start_time"],
                end_time=payload["end_time"],
                keyframe_paths=relative_keyframe_paths,
                thumbnail_paths=relative_thumbnail_paths,
                captions=scene_captions,
                embeddings=scene_embeddings,
                best_frame_index=best_frame_index,
                keyframe_path=relative_keyframe_paths[best_frame_index],
                thumbnail_path=relative_thumbnail_paths[best_frame_index],
                caption=scene_captions[best_frame_index],
                embedding=_normalized_mean_embedding(scene_embeddings),
                retrieval_text=retrieval_text,
                index_key=f"scene:{media.id}:{payload['scene_index']}",
            )
        )

    session.add_all(created_scenes)
    media.caption = _truncate_text(_join_unique_non_empty([scene.caption for scene in created_scenes], max_items=3), 200)
    media.retrieval_text = _truncate_text(
        _join_unique_non_empty([scene.retrieval_text for scene in created_scenes], max_items=10),
        1000,
    )
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


def _normalized_mean_embedding(embeddings: list[list[float]]) -> list[float] | None:
    normalized_embeddings: list[list[float]] = []
    for embedding in embeddings:
        norm = math.sqrt(sum(component * component for component in embedding))
        if norm <= 0:
            continue
        normalized_embeddings.append([component / norm for component in embedding])

    if not normalized_embeddings:
        return None

    dimension = len(normalized_embeddings[0])
    mean_embedding = [0.0] * dimension
    for embedding in normalized_embeddings:
        for index, component in enumerate(embedding):
            mean_embedding[index] += component

    count = len(normalized_embeddings)
    mean_embedding = [component / count for component in mean_embedding]
    mean_norm = math.sqrt(sum(component * component for component in mean_embedding))
    if mean_norm <= 0:
        return None

    return [component / mean_norm for component in mean_embedding]
