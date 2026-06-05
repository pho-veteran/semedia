from __future__ import annotations

import json
import mimetypes
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import MediaItem, ProcessingStatus


@dataclass
class SeedEvaluationAssetResult:
    asset_id: str
    filename: str
    status: str
    media_id: int | None = None
    caption: str | None = None
    skipped: bool = False
    detail: str | None = None


class SeedEvaluationError(RuntimeError):
    pass


class SeedEvaluationConcurrentError(SeedEvaluationError):
    pass


class SeedEvaluationMissingCorpusError(SeedEvaluationError):
    pass


class SeedEvaluationTimeoutError(SeedEvaluationError):
    pass


class SeedEvaluationLock:
    def __init__(self) -> None:
        self._locked = False

    def acquire(self) -> bool:
        if self._locked:
            return False
        self._locked = True
        return True

    def release(self) -> None:
        self._locked = False


DEFAULT_TIMEOUT_SECONDS = 300


def evaluation_manifest_file(evaluation_dir: Path) -> Path:
    return evaluation_dir / "asset_manifest.json"


def evaluation_assets_dir(evaluation_dir: Path) -> Path:
    return evaluation_dir / "assets"


def load_asset_manifest(evaluation_dir: Path) -> list[dict]:
    manifest_file = evaluation_manifest_file(evaluation_dir)
    assets_dir = evaluation_assets_dir(evaluation_dir)
    if not manifest_file.exists():
        raise SeedEvaluationMissingCorpusError(f"Asset manifest not found: {manifest_file}")
    if not assets_dir.exists():
        raise SeedEvaluationMissingCorpusError(f"Assets directory not found: {assets_dir}")

    manifest = json.loads(manifest_file.read_text())
    for item in manifest:
        filename = item["filename"]
        file_path = assets_dir / filename
        if not file_path.exists():
            raise SeedEvaluationMissingCorpusError(f"Manifest references missing file: {file_path}")
    return manifest


def upload_file(base_url: str, file_path: Path) -> dict:
    boundary = f"----SemediaBoundary{uuid4().hex}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()

    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)

    request = urllib.request.Request(
        f"{base_url}/api/v1/media/upload/",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
        if response.status != 201:
            raise SeedEvaluationError(f"Upload failed for {file_path.name}: {response.status} {payload}")
        return payload


def poll_media(base_url: str, media_id: int, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        request = urllib.request.Request(f"{base_url}/api/v1/media/{media_id}/", method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        state = payload["status"]
        if state in {"completed", "failed"}:
            return payload
        time.sleep(5)
    raise SeedEvaluationTimeoutError(f"Timed out waiting for media {media_id} to finish processing.")


def find_existing_media(session: Session, filename: str) -> MediaItem | None:
    return session.execute(
        select(MediaItem)
        .where(MediaItem.original_filename == filename)
        .order_by(MediaItem.id.desc())
    ).scalar_one_or_none()


def seed_evaluation_media(
    *,
    evaluation_dir: Path,
    base_url: str,
    session: Session,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    manifest = load_asset_manifest(evaluation_dir)
    assets_dir = evaluation_assets_dir(evaluation_dir)
    started_at = time.time()

    results: list[SeedEvaluationAssetResult] = []
    uploaded = 0
    completed = 0
    failed = 0
    skipped = 0

    for item in manifest:
        filename = item["filename"]
        asset_id = item["asset_id"]
        existing = find_existing_media(session, filename)
        if existing is not None and existing.status == ProcessingStatus.COMPLETED:
            skipped += 1
            results.append(
                SeedEvaluationAssetResult(
                    asset_id=asset_id,
                    filename=filename,
                    status=str(existing.status),
                    media_id=existing.id,
                    caption=existing.caption,
                    skipped=True,
                    detail="Already seeded.",
                )
            )
            continue

        file_path = assets_dir / filename
        upload_result = upload_file(base_url, file_path)
        media_id = int(upload_result["data"]["id"])
        uploaded += 1
        detail = poll_media(base_url, media_id, timeout_seconds=timeout_seconds)
        status = str(detail["status"])
        if status == ProcessingStatus.COMPLETED:
            completed += 1
        elif status == ProcessingStatus.FAILED:
            failed += 1
        results.append(
            SeedEvaluationAssetResult(
                asset_id=asset_id,
                filename=filename,
                media_id=media_id,
                status=status,
                caption=detail.get("caption"),
                detail=detail.get("error_message") or None,
            )
        )
        session.expire_all()

    elapsed_seconds = round(time.time() - started_at, 2)
    return {
        "message": "Evaluation media seeding finished.",
        "total": len(manifest),
        "uploaded": uploaded,
        "completed": completed,
        "failed": failed,
        "skipped": skipped,
        "elapsed_seconds": elapsed_seconds,
        "results": [result.__dict__ for result in results],
    }
