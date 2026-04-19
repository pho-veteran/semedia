from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4


def _request(
    method: str,
    url: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    expect_json: bool = True,
):
    request = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
        if not expect_json:
            return response.status, payload.decode("utf-8", errors="replace"), dict(response.headers)
        return response.status, json.loads(payload.decode("utf-8")), dict(response.headers)


def _build_multipart(
    file_path: Path,
    *,
    field_name: str = "file",
    extra_fields: dict[str, str] | None = None,
) -> tuple[bytes, str]:
    boundary = f"----SemediaBoundary{uuid4().hex}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()

    parts: list[bytes] = []
    for key, value in (extra_fields or {}).items():
        parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode("utf-8"),
            ]
        )

    parts.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8"),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _upload_file(base_url: str, file_path: Path) -> dict:
    body, content_type = _build_multipart(file_path)
    status, payload, _headers = _request(
        "POST",
        f"{base_url}/api/v1/media/upload/",
        body=body,
        headers={"Content-Type": content_type},
    )
    if status != 201:
        raise RuntimeError(f"Upload failed for {file_path.name}: {status} {payload}")
    return payload


def _search_by_image(base_url: str, file_path: Path, top_k: int = 5) -> dict:
    body, content_type = _build_multipart(file_path, extra_fields={"top_k": str(top_k)})
    status, payload, _headers = _request(
        "POST",
        f"{base_url}/api/v1/search/by-image/",
        body=body,
        headers={"Content-Type": content_type},
    )
    if status != 200:
        raise RuntimeError(f"Image search failed for {file_path.name}: {status} {payload}")
    return payload


def _poll_media(base_url: str, media_id: int, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        _status, payload, _headers = _request("GET", f"{base_url}/api/v1/media/{media_id}/")
        state = payload["status"]
        print(f"[poll] media={media_id} status={state}")
        if state in {"completed", "failed"}:
            return payload
        time.sleep(5)
    raise TimeoutError(f"Timed out waiting for media {media_id} to finish processing.")


def _delete_media(base_url: str, media_id: int) -> None:
    request = urllib.request.Request(f"{base_url}/api/v1/media/{media_id}/", method="DELETE")
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 204:
            raise RuntimeError(f"Delete failed for media {media_id}: HTTP {response.status}")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an end-to-end smoke test against the Semedia stack.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:4173")
    parser.add_argument("--image-path", default="Semedia/testing/smoke-assets/red-pixel.png")
    parser.add_argument("--video-path", default="Semedia/testing/smoke-assets/sample-video.mp4")
    parser.add_argument("--timeout-seconds", type=int, default=240)
    args = parser.parse_args()

    image_path = Path(args.image_path).resolve()
    video_path = Path(args.video_path).resolve()
    _assert(image_path.exists(), f"Image asset not found: {image_path}")
    _assert(video_path.exists(), f"Video asset not found: {video_path}")

    print("[check] frontend")
    frontend_status, frontend_html, _headers = _request("GET", args.frontend_url, expect_json=False)
    _assert(frontend_status == 200, "Frontend did not return HTTP 200.")
    _assert("Semedia" in frontend_html, "Frontend HTML does not look like the Semedia app.")

    print("[check] gateway health")
    status, payload, _headers = _request("GET", f"{args.base_url}/api/v1/health/")
    _assert(status == 200, "Gateway health check failed.")
    _assert(payload["status"] == "healthy", "Gateway did not report healthy.")

    print("[check] runtime")
    status, payload, _headers = _request("GET", f"{args.base_url}/api/v1/runtime/")
    _assert(status == 200, "Runtime endpoint failed.")
    _assert(payload["selected_device"] in {"cpu", "cuda"}, "Unexpected selected_device value.")

    print("[upload] image")
    image_upload = _upload_file(args.base_url, image_path)
    image_id = image_upload["data"]["id"]
    image_detail = _poll_media(args.base_url, image_id, args.timeout_seconds)
    _assert(image_detail["status"] == "completed", f"Image processing failed: {image_detail.get('error_message', '')}")

    print("[upload] video")
    video_upload = _upload_file(args.base_url, video_path)
    video_id = video_upload["data"]["id"]
    video_detail = _poll_media(args.base_url, video_id, args.timeout_seconds)
    _assert(video_detail["status"] == "completed", f"Video processing failed: {video_detail.get('error_message', '')}")
    _assert(video_detail["scene_count"] >= 1, "Processed video did not produce any scenes.")

    print("[search] gateway")
    status, search_payload, _headers = _request(
        "POST",
        f"{args.base_url}/api/v1/search/",
        body=json.dumps({"query_text": "red background", "top_k": 5}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    _assert(status == 200, "Search request failed.")
    _assert(search_payload["count"] >= 1, "Search returned no results.")
    _assert(
        any(result["media_id"] == video_id for result in search_payload["results"]),
        "Search results did not include the uploaded smoke-test video.",
    )

    print("[search] image query")
    image_search_payload = _search_by_image(args.base_url, image_path, top_k=5)
    _assert(image_search_payload["count"] >= 1, "Image-query search returned no results.")
    _assert(
        any(result["media_id"] == image_id for result in image_search_payload["results"]),
        "Image-query results did not include the uploaded smoke-test image.",
    )

    print("[delete] uploaded media")
    _delete_media(args.base_url, video_id)
    _delete_media(args.base_url, image_id)

    _status, media_list, _headers = _request("GET", f"{args.base_url}/api/v1/media/")
    remaining_ids = {item["id"] for item in media_list["results"]}
    _assert(image_id not in remaining_ids, "Uploaded smoke-test image still exists after delete.")
    _assert(video_id not in remaining_ids, "Uploaded smoke-test video still exists after delete.")

    print("[done] smoke test passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print(f"[http-error] {exc.code}: {exc.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        raise
