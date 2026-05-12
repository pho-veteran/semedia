from __future__ import annotations

import json
from pathlib import Path

import pytest

from testing.evaluation.benchmark_validation import (
    DEFAULT_JUDGMENT_POLICY,
    audit_log_has_blockers,
    can_sign_off_benchmark,
    select_targeted_rerun_pairs,
    validate_audit_log_entry,
    validate_benchmark_artifacts,
    validate_query_entry,
    validate_scene_key,
)


def test_validate_scene_key_accepts_canonical_scene_key():
    validate_scene_key("scene:vid-train-passing-01.webm:1")


def test_validate_scene_key_rejects_legacy_numeric_scene_id():
    with pytest.raises(ValueError):
        validate_scene_key("scene:12")


def test_validate_query_entry_accepts_wrapped_benchmark_entry():
    validate_query_entry(
        {
            "query_id": "q001",
            "query_text": "train passing",
            "query_type": "action",
            "judged": True,
            "relevant_media_ids": [],
            "relevant_scene_ids": ["scene:vid-train-passing-01.webm:1"],
            "media_type_target": "video",
            "difficulty": "easy",
            "tags": ["transport"],
            "notes": "Manual review: direct match in the locked corpus.",
        }
    )


def test_validate_audit_log_entry_requires_locked_at_and_disposition():
    validate_audit_log_entry(
        {
            "reviewer": "maintainer",
            "asset_id": "vid-train-passing-01",
            "scene_key": "scene:vid-train-passing-01.webm:1",
            "caption_status": "usable",
            "linked_failure_query_ids": [],
            "disposition": "accept",
            "locked_at": "2026-05-11T00:00:00Z",
        }
    )


def test_validate_benchmark_artifacts_requires_wrapped_queries(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "vid-train-passing-01.webm").write_bytes(b"fake")
    manifest_file = tmp_path / "asset_manifest.json"
    manifest_file.write_text(
        json.dumps(
            [
                {
                    "asset_id": "vid-train-passing-01",
                    "filename": "vid-train-passing-01.webm",
                    "media_type": "video",
                }
            ]
        )
    )
    queries_file = tmp_path / "queries.json"
    audit_log_file = tmp_path / "audit_log.json"
    queries_file.write_text(
        json.dumps(
            {
                "judgment_policy": DEFAULT_JUDGMENT_POLICY,
                "queries": [
                    {
                        "query_id": "q001",
                        "query_text": "train passing",
                        "query_type": "action",
                        "judged": True,
                        "relevant_media_ids": [],
                        "relevant_scene_ids": ["scene:vid-train-passing-01.webm:1"],
                        "media_type_target": "video",
                        "difficulty": "easy",
                        "tags": ["transport"],
                        "notes": "Manual review: direct match in the locked corpus.",
                    }
                ],
            }
        )
    )
    audit_log_file.write_text("[]")

    payload = validate_benchmark_artifacts(queries_file, audit_log_file)

    assert payload["judgment_policy"] == DEFAULT_JUDGMENT_POLICY
    assert len(payload["queries"]) == 1


def test_select_targeted_rerun_pairs_returns_linked_asset_query_pairs():
    audit_log = [
        {
            "reviewer": "maintainer",
            "asset_id": "vid-train-passing-01",
            "scene_key": "scene:vid-train-passing-01.webm:1",
            "caption_status": "problematic",
            "linked_failure_query_ids": ["q001", "q002"],
            "disposition": "fix_in_place",
            "locked_at": "2026-05-11T00:00:00Z",
        }
    ]

    assert select_targeted_rerun_pairs(audit_log) == [
        {"asset_id": "vid-train-passing-01", "query_id": "q001"},
        {"asset_id": "vid-train-passing-01", "query_id": "q002"},
    ]


def test_audit_log_has_blockers_flags_problematic_accept_entries():
    assert audit_log_has_blockers(
        [
            {
                "reviewer": "maintainer",
                "asset_id": "vid-train-passing-01",
                "scene_key": "scene:vid-train-passing-01.webm:1",
                "caption_status": "problematic",
                "linked_failure_query_ids": [],
                "disposition": "accept",
                "locked_at": "2026-05-11T00:00:00Z",
            }
        ]
    )
    assert not audit_log_has_blockers(
        [
            {
                "reviewer": "maintainer",
                "asset_id": "vid-train-passing-01",
                "scene_key": "scene:vid-train-passing-01.webm:1",
                "caption_status": "problematic",
                "linked_failure_query_ids": ["q001"],
                "disposition": "fix_in_place",
                "locked_at": "2026-05-11T00:00:00Z",
            }
        ]
    )


def test_can_sign_off_benchmark_requires_structural_validation_and_no_blockers():
    assert can_sign_off_benchmark([], True)
    assert can_sign_off_benchmark(
        [
            {
                "reviewer": "maintainer",
                "asset_id": "vid-train-passing-01",
                "scene_key": "scene:vid-train-passing-01.webm:1",
                "caption_status": "problematic",
                "linked_failure_query_ids": ["q001"],
                "disposition": "fix_in_place",
                "locked_at": "2026-05-11T00:00:00Z",
            }
        ],
        True,
    )
    assert not can_sign_off_benchmark(
        [
            {
                "reviewer": "maintainer",
                "asset_id": "vid-train-passing-01",
                "scene_key": "scene:vid-train-passing-01.webm:1",
                "caption_status": "problematic",
                "linked_failure_query_ids": [],
                "disposition": "accept",
                "locked_at": "2026-05-11T00:00:00Z",
            }
        ],
        True,
    )
    assert not can_sign_off_benchmark([], False)


def test_validate_audit_log_entry_rejects_inconsistent_problematic_accept():
    with pytest.raises(ValueError):
        validate_audit_log_entry(
            {
                "reviewer": "maintainer",
                "asset_id": "vid-train-passing-01",
                "scene_key": "scene:vid-train-passing-01.webm:1",
                "caption_status": "problematic",
                "linked_failure_query_ids": [],
                "disposition": "accept",
                "locked_at": "2026-05-11T00:00:00Z",
            }
        )
