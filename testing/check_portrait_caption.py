#!/usr/bin/env python3
"""Quick check: upload portrait and verify caption is not 'Image content unclear.'"""
import json
import mimetypes
import time
import urllib.request
from pathlib import Path
from uuid import uuid4


def upload_file(base_url: str, file_path: Path) -> dict:
    boundary = f"----Boundary{uuid4().hex}"
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
        return json.loads(response.read().decode("utf-8"))


def poll_media(base_url: str, media_id: int, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        request = urllib.request.Request(f"{base_url}/api/v1/media/{media_id}/", method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        state = payload["status"]
        if state in {"completed", "failed"}:
            return payload
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for media {media_id}")


if __name__ == "__main__":
    base_url = "http://127.0.0.1:8000"
    portrait_path = Path("Semedia/testing/evaluation/assets/img-portrait-01.jpg")

    print(f"[upload] {portrait_path.name}")
    result = upload_file(base_url, portrait_path)
    media_id = result["data"]["id"]
    print(f"  media_id={media_id}, polling...")

    detail = poll_media(base_url, media_id, timeout_seconds=180)
    caption = detail.get("caption", "")
    status = detail["status"]

    print(f"\n[result]")
    print(f"  status: {status}")
    print(f"  caption: {caption}")

    if caption == "Image content unclear.":
        print("\n[FAIL] Caption is still the fallback string")
        exit(1)
    elif caption and len(caption) > 0:
        print("\n[PASS] Caption is not the fallback")
        exit(0)
    else:
        print("\n[WARN] Caption is empty")
        exit(2)
