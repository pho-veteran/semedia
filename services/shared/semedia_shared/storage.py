from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .models import MediaItem


def ensure_media_root(settings) -> None:
    settings.media_root.mkdir(parents=True, exist_ok=True)


def _safe_filename(filename: str) -> str:
    original = Path(filename).name
    stem = Path(original).stem
    suffix = Path(original).suffix
    unique = uuid4().hex[:8]
    return f"{stem}_{unique}{suffix}"


def save_upload(settings, upload_file) -> tuple[str, int]:
    ensure_media_root(settings)
    dated_dir = settings.media_root / "originals" / datetime.utcnow().strftime("%Y/%m/%d")
    dated_dir.mkdir(parents=True, exist_ok=True)
    target = dated_dir / _safe_filename(upload_file.filename or "upload.bin")
    with target.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return str(target.relative_to(settings.media_root)).replace("\\", "/"), target.stat().st_size


def relative_to_media_root(settings, path_str: str) -> str:
    return str(Path(path_str).relative_to(settings.media_root)).replace("\\", "/")


def resolve_media_path(settings, relative_path: str) -> Path:
    return settings.media_root / relative_path


def media_url(settings, relative_path: str | None) -> str:
    if not relative_path:
        return ""
    normalized = relative_path.replace("\\", "/").lstrip("/")
    return f"{settings.media_base_url}/{normalized}"


def delete_path_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def delete_media_files(settings, media: MediaItem) -> None:
    for scene in list(media.scenes):
        if scene.keyframe_path:
            delete_path_if_exists(resolve_media_path(settings, scene.keyframe_path))
        if scene.thumbnail_path:
            delete_path_if_exists(resolve_media_path(settings, scene.thumbnail_path))

    if media.file_path:
        delete_path_if_exists(resolve_media_path(settings, media.file_path))
