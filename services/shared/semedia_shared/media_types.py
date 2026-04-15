from __future__ import annotations


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def infer_media_type(filename: str, content_type: str) -> str:
    normalized_name = filename.lower()

    for extension in IMAGE_EXTENSIONS:
        if normalized_name.endswith(extension):
            return "image"

    for extension in VIDEO_EXTENSIONS:
        if normalized_name.endswith(extension):
            return "video"

    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("video/"):
        return "video"

    raise ValueError(f"Unsupported media type for file `{filename}`.")


def validate_media_type(requested_type: str, inferred_type: str, filename: str) -> None:
    if requested_type != inferred_type:
        raise ValueError(f"Requested media_type `{requested_type}` does not match file `{filename}`.")
