from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .index_service import rebuild_keyword_index
from .models import MediaItem, ProcessingStatus, VideoScene


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def find_stuck_media(
    session: Session,
    *,
    now: datetime | None = None,
    pending_after: timedelta = timedelta(minutes=30),
    processing_after: timedelta = timedelta(hours=1),
) -> list[dict]:
    now = _as_utc(now) or datetime.now(timezone.utc)
    items = session.execute(select(MediaItem)).scalars().all()
    stuck: list[dict] = []
    for media in items:
        enqueued_at = _as_utc(media.enqueued_at)
        updated_at = _as_utc(media.updated_at)
        if media.status == ProcessingStatus.PENDING and enqueued_at and now - enqueued_at > pending_after:
            stuck.append({"media_id": media.id, "status": media.status, "reason": "pending_timeout"})
        elif media.status == ProcessingStatus.PROCESSING and updated_at and now - updated_at > processing_after:
            stuck.append({"media_id": media.id, "status": media.status, "reason": "processing_timeout"})
    return stuck


def scan_storage_consistency(settings, session: Session) -> dict:
    media_rows = session.execute(select(MediaItem).options(selectinload(MediaItem.scenes))).scalars().all()
    known_originals = {media.file_path for media in media_rows if media.file_path}
    orphaned_original_files: list[str] = []
    originals_root = settings.media_root / "originals"
    if originals_root.exists():
        for path in originals_root.rglob("*"):
            if path.is_file():
                relative_path = str(path.relative_to(settings.media_root)).replace("\\", "/")
                if relative_path not in known_originals:
                    orphaned_original_files.append(relative_path)

    missing_media_files = [
        {"media_id": media.id, "file_path": media.file_path}
        for media in media_rows
        if media.file_path and not (settings.media_root / media.file_path).exists()
    ]
    missing_scene_files = [
        {"scene_id": scene.id, "path": path}
        for media in media_rows
        for scene in media.scenes
        for path in [scene.keyframe_path, scene.thumbnail_path]
        if path and not (settings.media_root / path).exists()
    ]

    return {
        "orphaned_original_files": sorted(orphaned_original_files),
        "missing_media_files": missing_media_files,
        "missing_scene_files": missing_scene_files,
    }


def rebuild_keyword_index_repair(settings, session: Session) -> int:
    rebuild_keyword_index(settings, session)
    media_rows = session.execute(select(MediaItem).where(MediaItem.status == ProcessingStatus.COMPLETED)).scalars().all()
    scene_rows = session.execute(select(VideoScene)).scalars().all()
    return sum(1 for media in media_rows if media.media_type == "image" and media.caption) + sum(1 for scene in scene_rows if scene.caption)
