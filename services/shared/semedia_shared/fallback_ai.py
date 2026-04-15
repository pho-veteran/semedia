from __future__ import annotations

import hashlib
from pathlib import Path


def caption_from_path(path: str) -> str:
    suffix = Path(path).suffix.lower().lstrip(".") or "media"
    name = Path(path).stem.replace("-", " ").replace("_", " ")
    return f"{suffix} asset named {name}".strip()


def _hash_to_vector(value: str, size: int = 512) -> list[float]:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    numbers = []
    for index in range(size):
        byte = digest[index % len(digest)]
        numbers.append((byte / 255.0) * 2 - 1)
    return numbers


def embedding_from_path(path: str) -> list[float]:
    return _hash_to_vector(Path(path).name)


def embedding_from_text(text: str) -> list[float]:
    return _hash_to_vector(text)
