"""Load and parse benchmark query definitions."""
from __future__ import annotations

import json
from pathlib import Path


def load_queries(file_path: Path) -> list[dict]:
    payload = json.loads(file_path.read_text())
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "queries" in payload:
        return payload["queries"]
    raise ValueError(f"Cannot parse queries from {file_path}")
