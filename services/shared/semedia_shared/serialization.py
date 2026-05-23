from __future__ import annotations

from .models import MediaItem, VideoScene
from .storage import media_url


def scene_payload(settings, scene: VideoScene) -> dict:
    return {
        "id": scene.id,
        "scene_index": scene.scene_index,
        "start_time": scene.start_time,
        "end_time": scene.end_time,
        "keyframe_image": media_url(settings, scene.keyframe_path),
        "thumbnail_image": media_url(settings, scene.thumbnail_path),
        "caption": scene.caption or "",
        "index_key": scene.index_key or "",
    }


def media_summary(settings, media: MediaItem) -> dict:
    return {
        "id": media.id,
        "file": media_url(settings, media.file_path),
        "original_filename": media.original_filename,
        "media_type": media.media_type,
        "mime_type": media.mime_type or "",
        "file_size": media.file_size,
        "status": media.status,
        "duration": media.duration,
        "caption": media.caption or "",
        "index_key": media.index_key or "",
        "uploaded_at": media.uploaded_at,
        "updated_at": media.updated_at,
        "enqueued_at": media.enqueued_at,
        "processed_at": media.processed_at,
        "scene_count": len(media.scenes),
    }


def media_detail(settings, media: MediaItem) -> dict:
    payload = media_summary(settings, media)
    payload["error_message"] = media.error_message or ""
    payload["scenes"] = [scene_payload(settings, scene) for scene in media.scenes]
    return payload
