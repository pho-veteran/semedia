from __future__ import annotations

import json
from pathlib import Path


def test_all_assets_are_manifested():
    evaluation_dir = Path(__file__).parent
    manifest_file = evaluation_dir / "asset_manifest.json"
    assets_dir = evaluation_dir / "assets"

    assert manifest_file.exists(), "Phase 7 requires testing/evaluation/asset_manifest.json"
    assert assets_dir.exists(), "Phase 7 requires testing/evaluation/assets/"

    manifest = json.loads(manifest_file.read_text())
    manifested_filenames = {item["filename"] for item in manifest}

    actual_files = {
        f.name
        for f in assets_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".mp4", ".webm"}
    }

    unmanifested = actual_files - manifested_filenames
    assert not unmanifested, (
        f"Found {len(unmanifested)} files in testing/evaluation/assets/ that are not in asset_manifest.json: "
        f"{sorted(unmanifested)}. The locked corpus must not drift from the manifest."
    )

    missing_files = manifested_filenames - actual_files
    assert not missing_files, (
        f"Found {len(missing_files)} files in asset_manifest.json that do not exist in assets/: "
        f"{sorted(missing_files)}. The manifest must reference only existing files."
    )
