#!/usr/bin/env python3
"""
Seed the media library with test assets for Phase 1 baseline evaluation.
"""
from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.request
from pathlib import Path
from uuid import uuid4


def upload_file(base_url: str, file_path: Path) -> dict:
    """Upload a file to Semedia gateway API."""
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
            raise RuntimeError(f"Upload failed for {file_path.name}: {response.status} {payload}")
        return payload


def poll_media(base_url: str, media_id: int, timeout_seconds: int) -> dict:
    """Poll media processing status until complete or failed."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        request = urllib.request.Request(f"{base_url}/api/v1/media/{media_id}/", method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        state = payload["status"]
        print(f"  [poll] media={media_id} status={state}")
        if state in {"completed", "failed"}:
            return payload
        time.sleep(5)
    raise TimeoutError(f"Timed out waiting for media {media_id} to finish processing.")


def main():
    base_url = "http://gateway-api:8000"
    evaluation_dir = Path(
        os.environ.get("SEMEDIA_EVALUATION_DIR", "/app/testing/evaluation")
    )
    manifest_file = evaluation_dir / "asset_manifest.json"
    assets_dir = evaluation_dir / "assets"

    if not manifest_file.exists():
        raise FileNotFoundError(f"Asset manifest not found: {manifest_file}")

    manifest = json.loads(manifest_file.read_text())
    print(f"Uploading {len(manifest)} files from manifest")

    for item in manifest:
        filename = item["filename"]
        file_path = assets_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Manifest references missing file: {file_path}")

        print(f"\n[upload] {filename} (asset_id={item['asset_id']})")
        result = upload_file(base_url, file_path)
        media_id = result["data"]["id"]
        detail = poll_media(base_url, media_id, timeout_seconds=300)
        print(
            json.dumps(
                {
                    "asset_id": item["asset_id"],
                    "filename": filename,
                    "media_id": media_id,
                    "status": detail["status"],
                    "caption": detail.get("caption"),
                }
            )
        )

    print("\n[done] Media seeding complete")


if __name__ == "__main__":
    main()
