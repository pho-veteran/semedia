from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_JUDGMENT_POLICY = {
    "path": "docs/metrics/evaluation_benchmark_rubric.md",
    "version": "2026-05-11",
}

ALLOWED_CAPTION_STATUSES = {"usable", "weak-but-acceptable", "problematic"}
ALLOWED_DISPOSITIONS = {"accept", "fix_in_place", "remove"}
ALLOWED_QUERY_TYPES = {"object", "action", "scene"}
ALLOWED_MEDIA_TARGETS = {"image", "video", "mixed"}
ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}
VIDEO_EXTENSIONS = (".webm", ".mp4", ".ogv")


def _load_json(file_path: Path) -> Any:
    return json.loads(file_path.read_text())


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate_timestamp(value: Any, *, field_name: str) -> None:
    _require(isinstance(value, str) and value.strip(), f"{field_name} must be a non-empty timestamp string")
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_scene_key(scene_key: str) -> None:
    _require(isinstance(scene_key, str), f"scene_key must be a string, got {type(scene_key).__name__}")
    parts = scene_key.split(":")
    _require(len(parts) == 3 and parts[0] == "scene", f"scene_key must be scene:<filename>:<scene_index>, got {scene_key}")
    _, filename, scene_index = parts
    _require(filename.endswith(VIDEO_EXTENSIONS), f"scene_key must reference a video filename, got {scene_key}")
    _require(scene_index.isdigit(), f"scene_key scene index must be numeric, got {scene_key}")


def normalize_relevant_id(value: Any, *, kind: str) -> str:
    _require(kind in {"media", "scene"}, f"Unknown identifier kind: {kind}")

    if kind == "media":
        if isinstance(value, int):
            return f"media:{value}"
        if isinstance(value, str) and value.startswith("media:"):
            return value
        if isinstance(value, str) and value.isdigit():
            return f"media:{value}"
        raise TypeError(f"Unsupported media identifier: {value!r}")

    if isinstance(value, int):
        return f"scene:{value}"
    if isinstance(value, str):
        if value.startswith("scene:"):
            validate_scene_key(value)
            return value
        if value.isdigit():
            return f"scene:{value}"
        return f"scene:{value}"
    raise TypeError(f"Unsupported scene identifier: {value!r}")


def load_benchmark_definition(file_path: Path, *, strict: bool = False) -> dict:
    payload = _load_json(file_path)

    if isinstance(payload, list):
        _require(not strict, f"{file_path} must use a top-level object with judgment_policy and queries")
        return {"judgment_policy": DEFAULT_JUDGMENT_POLICY, "queries": payload}

    _require(isinstance(payload, dict), f"{file_path} must contain a JSON object or array")
    _require(isinstance(payload.get("queries"), list), f"{file_path} must contain a top-level queries array")

    if strict:
        validate_judgment_policy(payload.get("judgment_policy"), file_path=file_path)
        validate_queries_payload(payload["queries"], file_path=file_path)

    return payload


def load_queries(file_path: Path) -> list[dict]:
    return load_benchmark_definition(file_path)["queries"]


def validate_judgment_policy(policy: Any, *, file_path: Path | None = None) -> None:
    location = f" in {file_path}" if file_path else ""
    _require(isinstance(policy, dict), f"judgment_policy must be an object{location}")
    _require(policy.get("path") == DEFAULT_JUDGMENT_POLICY["path"], f"judgment_policy.path must be {DEFAULT_JUDGMENT_POLICY['path']}{location}")
    _require(policy.get("version") == DEFAULT_JUDGMENT_POLICY["version"], f"judgment_policy.version must be {DEFAULT_JUDGMENT_POLICY['version']}{location}")


def validate_query_entry(query: Any, *, file_path: Path | None = None) -> None:
    location = f" in {file_path}" if file_path else ""
    _require(isinstance(query, dict), f"Each query must be an object{location}")

    required_fields = {
        "query_id",
        "query_text",
        "query_type",
        "judged",
        "relevant_media_ids",
        "relevant_scene_ids",
        "media_type_target",
        "difficulty",
        "tags",
        "notes",
    }
    _require(required_fields.issubset(query), f"Missing required query field(s){location}: {sorted(required_fields - set(query))}")
    _require(isinstance(query["query_id"], str) and query["query_id"].strip(), f"query_id must be a non-empty string{location}")
    _require(isinstance(query["query_text"], str) and query["query_text"].strip(), f"query_text must be a non-empty string{location}")
    _require(query["query_type"] in ALLOWED_QUERY_TYPES, f"query_type must be one of {sorted(ALLOWED_QUERY_TYPES)}{location}")
    _require(isinstance(query["judged"], bool), f"judged must be a boolean{location}")
    _require(isinstance(query["relevant_media_ids"], list), f"relevant_media_ids must be a list{location}")
    _require(isinstance(query["relevant_scene_ids"], list), f"relevant_scene_ids must be a list{location}")
    _require(query["media_type_target"] in ALLOWED_MEDIA_TARGETS, f"media_type_target must be one of {sorted(ALLOWED_MEDIA_TARGETS)}{location}")
    _require(query["difficulty"] in ALLOWED_DIFFICULTY, f"difficulty must be one of {sorted(ALLOWED_DIFFICULTY)}{location}")
    _require(isinstance(query["tags"], list), f"tags must be a list{location}")
    _require(isinstance(query["notes"], str) and query["notes"].strip(), f"notes must be a non-empty string{location}")

    for media_id in query["relevant_media_ids"]:
        _require(isinstance(media_id, int) and media_id > 0, f"relevant_media_ids must contain positive integers{location}")

    for scene_key in query["relevant_scene_ids"]:
        validate_scene_key(scene_key)


def validate_queries_payload(queries: Any, *, file_path: Path | None = None) -> None:
    _require(isinstance(queries, list), f"queries must be a list{'' if file_path is None else f' in {file_path}'}")
    for query in queries:
        validate_query_entry(query, file_path=file_path)


def _validate_asset_manifest(file_path: Path, manifest_file: Path) -> None:
    _require(manifest_file.exists(), f"{manifest_file} must exist for locked evaluation assets")
    manifest = _load_json(manifest_file)
    _require(isinstance(manifest, list), f"{manifest_file} must contain a JSON array")

    actual_assets_dir = file_path.parent / "assets"
    _require(actual_assets_dir.exists(), f"{actual_assets_dir} must exist for locked evaluation assets")

    manifested_filenames: set[str] = set()
    for item in manifest:
        _require(isinstance(item, dict), f"Each asset manifest entry must be an object in {manifest_file}")
        _require(isinstance(item.get("filename"), str) and item["filename"].strip(), f"Each asset manifest entry must include a filename in {manifest_file}")
        manifested_filenames.add(item["filename"])

    actual_filenames = {
        item.name
        for item in actual_assets_dir.iterdir()
        if item.is_file() and item.suffix.lower() in {".jpg", ".jpeg", ".png", ".mp4", ".webm", ".ogv"}
    }

    _require(not (actual_filenames - manifested_filenames), f"Found unmanifested asset files in {actual_assets_dir}: {sorted(actual_filenames - manifested_filenames)}")
    _require(not (manifested_filenames - actual_filenames), f"Found missing asset files referenced by {manifest_file}: {sorted(manifested_filenames - actual_filenames)}")


def validate_queries_file(file_path: Path) -> dict:
    payload = load_benchmark_definition(file_path, strict=True)
    _require(isinstance(payload.get("queries"), list), f"{file_path} must contain a top-level queries array")
    _validate_asset_manifest(file_path, file_path.with_name("asset_manifest.json"))
    return payload


def validate_audit_log_entry(entry: Any, *, file_path: Path | None = None) -> None:
    location = f" in {file_path}" if file_path else ""
    _require(isinstance(entry, dict), f"Each audit log entry must be an object{location}")

    required_fields = {
        "reviewer",
        "asset_id",
        "scene_key",
        "caption_status",
        "linked_failure_query_ids",
        "disposition",
        "locked_at",
    }
    _require(required_fields.issubset(entry), f"Missing required audit log field(s){location}: {sorted(required_fields - set(entry))}")
    _require(isinstance(entry["reviewer"], str) and entry["reviewer"].strip(), f"reviewer must be a non-empty string{location}")
    _require(isinstance(entry["asset_id"], (int, str)) and str(entry["asset_id"]).strip(), f"asset_id must be a non-empty value{location}")
    if entry["scene_key"] is not None:
        validate_scene_key(entry["scene_key"])
    _require(entry["caption_status"] in ALLOWED_CAPTION_STATUSES, f"caption_status must be one of {sorted(ALLOWED_CAPTION_STATUSES)}{location}")
    _require(isinstance(entry["linked_failure_query_ids"], list), f"linked_failure_query_ids must be a list{location}")
    _require(entry["disposition"] in ALLOWED_DISPOSITIONS, f"disposition must be one of {sorted(ALLOWED_DISPOSITIONS)}{location}")
    if entry["caption_status"] == "problematic":
        _require(entry["linked_failure_query_ids"], f"problematic captions must link at least one failure query{location}")
        _require(entry["disposition"] in {"fix_in_place", "remove"}, f"problematic captions must be fixed in place or removed{location}")
    _validate_timestamp(entry["locked_at"], field_name=f"locked_at{location}")


def validate_audit_log_payload(entries: Any, *, file_path: Path | None = None) -> None:
    _require(isinstance(entries, list), f"audit_log must be a list{'' if file_path is None else f' in {file_path}'}")
    for entry in entries:
        validate_audit_log_entry(entry, file_path=file_path)


def validate_audit_log_file(file_path: Path) -> list[dict]:
    payload = _load_json(file_path)
    validate_audit_log_payload(payload, file_path=file_path)
    return payload


def select_targeted_rerun_pairs(audit_log: list[dict]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    for entry in audit_log:
        if entry["disposition"] != "fix_in_place":
            continue
        for query_id in entry["linked_failure_query_ids"]:
            pairs.append({"asset_id": str(entry["asset_id"]), "query_id": str(query_id)})
    return pairs


def audit_log_has_blockers(audit_log: list[dict]) -> bool:
    return any(entry["caption_status"] == "problematic" and entry["disposition"] == "accept" for entry in audit_log)


def can_sign_off_benchmark(audit_log: list[dict], structural_validation_ok: bool) -> bool:
    return structural_validation_ok and not audit_log_has_blockers(audit_log)


def validate_benchmark_artifacts(queries_file: Path, audit_log_file: Path) -> dict:
    queries_payload = validate_queries_file(queries_file)
    audit_log_payload = validate_audit_log_file(audit_log_file)
    return {"queries": queries_payload["queries"], "judgment_policy": queries_payload["judgment_policy"], "audit_log": audit_log_payload}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Semedia benchmark artifacts.")
    parser.add_argument("--queries", default=Path(__file__).with_name("queries.json"), type=Path)
    parser.add_argument("--audit-log", default=Path(__file__).with_name("audit_log.json"), type=Path)
    args = parser.parse_args()

    validate_benchmark_artifacts(args.queries, args.audit_log)
    print(f"Validated benchmark artifacts: {args.queries} and {args.audit_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
