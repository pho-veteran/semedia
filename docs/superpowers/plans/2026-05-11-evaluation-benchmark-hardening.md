# Evaluation Benchmark Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the Semedia evaluation benchmark with canonical scene-key handling, schema validation, a structured audit log, and lock-workflow verification without changing retrieval behavior.

**Architecture:** Keep benchmark policy, validation, and evaluation concerns separate. Put benchmark-artifact validation and lock-workflow helpers in a small support module under `testing/evaluation/`, keep `evaluate_search.py` focused on metrics and identifier handling, and gate `run_evaluation.py` through a preflight validation step so evaluation cannot start until the benchmark artifacts are structurally sound. Treat the rubric doc and `queries.json` policy metadata as the source of truth for judgment rules.

**Tech Stack:** Python 3, pytest, Docker Compose, JSON artifacts, Markdown docs

---

## Execution Notes

- Do **not** commit unless the user explicitly asks.
- Run evaluation and test commands through Docker Compose.
- Keep retrieval weights, embedding logic, and ranking code out of scope.
- Keep the benchmark hardening focused on `Semedia/testing/evaluation/` and `Semedia/docs/metrics/`.

## File Structure

### New files
- `testing/evaluation/benchmark_validation.py` — benchmark-artifact schema validation, canonical scene-key checks, and lock-workflow helpers.
- `testing/evaluation/validate_benchmark_artifacts.py` — CLI entry point for pre-lock and CI validation.
- `testing/evaluation/audit_log.json` — structured benchmark lock audit history.
- `testing/evaluation/test_benchmark_validation.py` — validation and lock-workflow regression tests.
- `docs/metrics/evaluation_benchmark_rubric.md` — canonical benchmark judgment policy and caption-audit rubric.

### Modified files
- `testing/evaluation/queries.json` — move to a top-level `judgment_policy` + `queries` schema and keep stable scene-key judgments canonical.
- `testing/evaluation/evaluate_search.py` — keep evaluation metrics, but fix canonical scene-key matching and query loading.
- `testing/evaluation/run_evaluation.py` — call benchmark validation before evaluation starts.
- `testing/evaluation/populate_judgments.py` — read and write the new `queries.json` wrapper object.
- `testing/evaluation/test_evaluate_search.py` — update evaluator regression coverage for stable scene keys and the new query payload shape.

### Files intentionally left unchanged
- `services/` production retrieval code, except for any indirect test failures caused by evaluator fixes.
- Ranking weights, embeddings, and caption-generation logic.
- `testing/smoke-assets/` and smoke workflow code.

---

### Task 1: Add the canonical benchmark policy and wrap the query dataset

**Files:**
- Create: `docs/metrics/evaluation_benchmark_rubric.md`
- Create: `testing/evaluation/audit_log.json`
- Modify: `testing/evaluation/queries.json`
- Modify: `testing/evaluation/populate_judgments.py`
- Test: `testing/evaluation/test_benchmark_validation.py`

- [ ] **Step 1: Write the failing schema tests**

Add these tests to `testing/evaluation/test_benchmark_validation.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from testing.evaluation.benchmark_validation import load_queries_payload


def test_queries_payload_declares_judgment_policy_and_queries():
    queries_file = Path(__file__).with_name("queries.json")
    payload = json.loads(queries_file.read_text())

    assert payload["judgment_policy"] == {
        "path": "docs/metrics/evaluation_benchmark_rubric.md",
        "version": "2026-05-11-v1",
    }
    assert isinstance(payload["queries"], list)
    assert payload["queries"], "The locked benchmark still needs judged queries"


def test_load_queries_payload_returns_query_rows(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            {
                "judgment_policy": {
                    "path": "docs/metrics/evaluation_benchmark_rubric.md",
                    "version": "2026-05-11-v1",
                },
                "queries": [
                    {
                        "query_id": "q001",
                        "query_text": "train passing",
                        "query_type": "action",
                        "judged": True,
                        "relevant_media_ids": [],
                        "relevant_scene_ids": ["scene:vid-train-passing-01.webm:1"],
                        "media_type_target": "video",
                        "difficulty": "medium",
                        "tags": ["positive"],
                        "notes": "Manual review confirmed the train scene.",
                    }
                ],
            }
        )
    )

    payload = load_queries_payload(queries_file)

    assert payload["judgment_policy"]["version"] == "2026-05-11-v1"
    assert len(payload["queries"]) == 1
    assert payload["queries"][0]["relevant_scene_ids"] == ["scene:vid-train-passing-01.webm:1"]
```

- [ ] **Step 2: Run the schema tests to verify they fail**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_benchmark_validation.py -q
```

Expected: FAIL because `queries.json` still uses the old array-only shape and the new rubric file does not exist yet.

- [ ] **Step 3: Add the rubric doc and migrate `queries.json` to the wrapped schema**

Create `docs/metrics/evaluation_benchmark_rubric.md` with this structure:

```md
# Semedia Evaluation Benchmark Rubric

**Version:** 2026-05-11-v1

## Judgment rules
- Object queries: the correct object class must be visually present.
- Action queries: the action must be visually depicted, not merely implied.
- Scene queries: the judged scene key must match the canonical identifier, not a legacy numeric ID.

## Caption audit statuses
- `usable`
- `weak-but-acceptable`
- `problematic`

## Escalation rule
A problematic caption blocks benchmark acceptance only when it can be directly linked to retrieval failure or measurable metric noise in the current run.

## Lock rule
The benchmark maintainer is the single approver for locking the benchmark after validation and audit review pass.
```

Rewrite `testing/evaluation/queries.json` from a raw array into this wrapper shape:

```json
{
  "judgment_policy": {
    "path": "docs/metrics/evaluation_benchmark_rubric.md",
    "version": "2026-05-11-v1"
  },
  "queries": [
    {
      "query_id": "q001",
      "query_text": "airplane",
      "query_type": "object",
      "judged": true,
      "relevant_media_ids": [1],
      "relevant_scene_ids": [],
      "media_type_target": "image",
      "difficulty": "easy",
      "tags": ["vehicle", "aviation"],
      "notes": "Manual review: the corpus includes a daylight airplane runway photo that directly matches this object query."
    }
    // keep the existing judged entries unchanged, just move them under queries[]
  ]
}
```

Create `testing/evaluation/audit_log.json` as a valid empty audit history to start:

```json
[]
```

Update `testing/evaluation/populate_judgments.py` so it reads and preserves the wrapper object instead of assuming a raw list:

```python
payload = json.loads(queries_file.read_text())
queries = payload["queries"] if isinstance(payload, dict) else payload

# ...manual review loop over queries...

if isinstance(payload, dict):
    payload["queries"] = queries
    queries_file.write_text(json.dumps(payload, indent=2))
else:
    queries_file.write_text(json.dumps(queries, indent=2))
```

- [ ] **Step 4: Run the schema tests to verify they pass**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_benchmark_validation.py -q
```

Expected: PASS after the rubric doc exists and the dataset uses the wrapped schema.

---

### Task 2: Add benchmark artifact validation and gate evaluation before it starts

**Files:**
- Create: `testing/evaluation/benchmark_validation.py`
- Create: `testing/evaluation/validate_benchmark_artifacts.py`
- Modify: `testing/evaluation/run_evaluation.py`
- Test: `testing/evaluation/test_benchmark_validation.py`

- [ ] **Step 1: Write the failing validation tests**

Extend `testing/evaluation/test_benchmark_validation.py` with these tests:

```python
import pytest

from testing.evaluation.benchmark_validation import validate_benchmark_artifacts


def test_validate_benchmark_artifacts_rejects_legacy_numeric_scene_ids(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            {
                "judgment_policy": {
                    "path": "docs/metrics/evaluation_benchmark_rubric.md",
                    "version": "2026-05-11-v1",
                },
                "queries": [
                    {
                        "query_id": "q001",
                        "query_text": "train passing",
                        "query_type": "action",
                        "judged": True,
                        "relevant_media_ids": [],
                        "relevant_scene_ids": [7],
                        "media_type_target": "video",
                        "difficulty": "medium",
                        "tags": ["positive"],
                        "notes": "Manual review confirmed the train scene.",
                    }
                ],
            }
        )
    )
    manifest_file = tmp_path / "asset_manifest.json"
    manifest_file.write_text(json.dumps([]))
    audit_log_file = tmp_path / "audit_log.json"
    audit_log_file.write_text(json.dumps([]))

    with pytest.raises(ValueError, match="canonical scene-key"):
        validate_benchmark_artifacts(queries_file, manifest_file, audit_log_file)


def test_validate_benchmark_artifacts_rejects_invalid_audit_log_schema(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            {
                "judgment_policy": {
                    "path": "docs/metrics/evaluation_benchmark_rubric.md",
                    "version": "2026-05-11-v1",
                },
                "queries": [],
            }
        )
    )
    manifest_file = tmp_path / "asset_manifest.json"
    manifest_file.write_text(json.dumps([]))
    audit_log_file = tmp_path / "audit_log.json"
    audit_log_file.write_text(json.dumps([
        {
            "reviewer": "",
            "asset_id": "img-cat-01",
            "caption_status": "problematic",
            "linked_failure_query_ids": [],
            "disposition": "accept",
            "locked_at": "2026-05-11T12:00:00Z",
        }
    ]))

    with pytest.raises(ValueError, match="scene_key"):
        validate_benchmark_artifacts(queries_file, manifest_file, audit_log_file)
```

- [ ] **Step 2: Run the validation tests to verify they fail**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_benchmark_validation.py -q
```

Expected: FAIL because the validation helpers do not exist yet.

- [ ] **Step 3: Implement the validation helpers and CLI wrapper**

Create `testing/evaluation/benchmark_validation.py` with helpers like this:

```python
from __future__ import annotations

import json
from pathlib import Path


def load_queries_payload(file_path: Path) -> dict:
    payload = json.loads(file_path.read_text())
    if isinstance(payload, list):
        return {
            "judgment_policy": None,
            "queries": payload,
        }
    return payload


def validate_scene_key(scene_key: str) -> None:
    parts = scene_key.split(":")
    if len(parts) != 3 or parts[0] != "scene" or not parts[2].isdigit():
        raise ValueError(f"Expected canonical scene-key format scene:<filename>:<scene_index>, got {scene_key}")


def validate_benchmark_artifacts(queries_path: Path, manifest_path: Path, audit_log_path: Path) -> None:
    payload = load_queries_payload(queries_path)
    policy = payload.get("judgment_policy")
    if not policy or policy.get("path") != "docs/metrics/evaluation_benchmark_rubric.md" or not policy.get("version"):
        raise ValueError("queries.json must declare judgment_policy.path and judgment_policy.version")

    for query in payload["queries"]:
        for scene_key in query.get("relevant_scene_ids", []):
            if not isinstance(scene_key, str):
                raise ValueError("Scene judgments must use canonical scene-key strings")
            validate_scene_key(scene_key)

    audit_log = json.loads(audit_log_path.read_text())
    if not isinstance(audit_log, list):
        raise ValueError("audit_log.json must contain a list of audit entries")

    required_fields = {
        "reviewer",
        "asset_id",
        "scene_key",
        "caption_status",
        "linked_failure_query_ids",
        "disposition",
        "locked_at",
    }
    for entry in audit_log:
        if not required_fields.issubset(entry):
            raise ValueError("audit_log.json entries are missing required fields")
        if entry["scene_key"] is not None:
            validate_scene_key(entry["scene_key"])
        if entry["caption_status"] not in {"usable", "weak-but-acceptable", "problematic"}:
            raise ValueError("Invalid caption_status")
        if entry["disposition"] not in {"accept", "fix_in_place", "remove"}:
            raise ValueError("Invalid disposition")
```

Create `testing/evaluation/validate_benchmark_artifacts.py` as a thin CLI wrapper around that helper.

Update `testing/evaluation/run_evaluation.py` so it validates the benchmark artifacts before loading queries or calling the search API:

```python
from .benchmark_validation import validate_benchmark_artifacts


queries_file = Path(args.queries) if args.queries else Path(__file__).parent / "queries.json"
manifest_file = Path(__file__).parent / "asset_manifest.json"
audit_log_file = Path(__file__).parent / "audit_log.json"

validate_benchmark_artifacts(queries_file, manifest_file, audit_log_file)
queries = load_queries(queries_file)
```

- [ ] **Step 4: Run the validation tests and CLI to verify they pass**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_benchmark_validation.py -q
```

Then run:

```bash
docker compose --profile test run --rm --build service-tests python testing/evaluation/validate_benchmark_artifacts.py
```

Expected: PASS for the tests and `benchmark-artifacts-ok` (or the equivalent success message) from the CLI.

---

### Task 3: Fix canonical scene-key matching in evaluation

**Files:**
- Modify: `testing/evaluation/evaluate_search.py`
- Modify: `testing/evaluation/test_evaluate_search.py`

- [ ] **Step 1: Write the failing stable-scene-key regression test**

Add this test to `testing/evaluation/test_evaluate_search.py`:

```python
def test_run_evaluation_prefers_stable_scene_keys_when_present(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            {
                "judgment_policy": {
                    "path": "docs/metrics/evaluation_benchmark_rubric.md",
                    "version": "2026-05-11-v1",
                },
                "queries": [
                    {
                        "query_id": "q001",
                        "query_text": "train passing",
                        "query_type": "action",
                        "judged": True,
                        "relevant_media_ids": [],
                        "relevant_scene_ids": ["scene:vid-train-passing-01.webm:1"],
                        "media_type_target": "video",
                        "difficulty": "medium",
                        "tags": ["positive"],
                        "notes": "Manual review confirmed the train scene.",
                    }
                ],
            }
        )
    )

    def mock_search(query_text, top_k):
        return [
            {
                "media_id": 10,
                "scene_id": 5,
                "scene_key": "scene:vid-train-passing-01.webm:1",
                "score": 80.0,
            }
        ]

    results = run_evaluation(queries_file, mock_search, k=10, include_per_query=True)

    assert results["num_queries"] == 1
    assert results["mean_recall@10"] == 1.0
    assert results["per_query"][0]["retrieved_ids"] == ["scene:vid-train-passing-01.webm:1"]
```

- [ ] **Step 2: Run the evaluator test to verify it fails**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_evaluate_search.py::test_run_evaluation_prefers_stable_scene_keys_when_present -q
```

Expected: FAIL because the evaluator still double-prefixes `scene:` when building relevance IDs.

- [ ] **Step 3: Make the minimal evaluator change**

Update the relevance-ID construction in `testing/evaluation/evaluate_search.py` so stable scene keys are used as-is:

```python
relevant_media_ids = set(query.get("relevant_media_ids", []))
relevant_scene_ids = set(query.get("relevant_scene_ids", []))
relevant_ids = {
    *(f"media:{item_id}" for item_id in relevant_media_ids),
    *relevant_scene_ids,
}
```

Keep `_result_identifier()` preferring `scene_key` when present.

- [ ] **Step 4: Run the evaluator test to verify it passes**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_evaluate_search.py::test_run_evaluation_prefers_stable_scene_keys_when_present -q
```

Expected: PASS, with the retrieved stable scene key matching the judged stable scene key exactly.

---

### Task 4: Add audit-log escalation helpers and targeted rerun selection

**Files:**
- Modify: `testing/evaluation/benchmark_validation.py`
- Modify: `testing/evaluation/test_benchmark_validation.py`

- [ ] **Step 1: Write the failing lock-workflow tests**

Add these tests to `testing/evaluation/test_benchmark_validation.py`:

```python
from testing.evaluation.benchmark_validation import targeted_rerun_query_ids, can_sign_off


def test_targeted_rerun_query_ids_only_uses_linked_failures():
    audit_log = [
        {
            "reviewer": "bench-maintainer",
            "asset_id": "vid-train-passing-01",
            "scene_key": "scene:vid-train-passing-01.webm:1",
            "caption_status": "problematic",
            "linked_failure_query_ids": ["q056", "q057"],
            "disposition": "fix_in_place",
            "locked_at": "2026-05-11T12:00:00Z",
        },
        {
            "reviewer": "bench-maintainer",
            "asset_id": "img-cat-01",
            "scene_key": None,
            "caption_status": "usable",
            "linked_failure_query_ids": [],
            "disposition": "accept",
            "locked_at": "2026-05-11T12:10:00Z",
        },
    ]

    assert targeted_rerun_query_ids(audit_log) == ["q056", "q057"]


def test_can_sign_off_requires_no_unresolved_problematic_entries():
    audit_log = [
        {
            "reviewer": "bench-maintainer",
            "asset_id": "vid-waterfall-01",
            "scene_key": "scene:vid-waterfall-01.webm:0",
            "caption_status": "problematic",
            "linked_failure_query_ids": ["q060"],
            "disposition": "fix_in_place",
            "locked_at": "2026-05-11T12:00:00Z",
        }
    ]

    assert can_sign_off(audit_log, structural_validation_ok=False) is False
    assert can_sign_off(audit_log, structural_validation_ok=True) is False
```

- [ ] **Step 2: Run the workflow tests to verify they fail**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_benchmark_validation.py -q
```

Expected: FAIL until the targeted rerun and sign-off helpers exist.

- [ ] **Step 3: Implement the lock-workflow helpers**

Extend `testing/evaluation/benchmark_validation.py` with helpers like these:

```python
from typing import Any


def targeted_rerun_query_ids(audit_log: list[dict[str, Any]]) -> list[str]:
    query_ids = []
    for entry in audit_log:
        if entry["disposition"] == "fix_in_place":
            for query_id in entry["linked_failure_query_ids"]:
                if query_id not in query_ids:
                    query_ids.append(query_id)
    return query_ids


def can_sign_off(audit_log: list[dict[str, Any]], structural_validation_ok: bool) -> bool:
    if not structural_validation_ok:
        return False
    return all(
        entry["caption_status"] != "problematic" or entry["disposition"] in {"accept", "remove"}
        for entry in audit_log
    )
```

Keep the default rerun scope targeted to linked failures only; a full rerun should remain a separate explicit decision.

- [ ] **Step 4: Run the workflow tests to verify they pass**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_benchmark_validation.py -q
```

Expected: PASS.

---

### Task 5: Verify the hardened benchmark path end to end

**Files:**
- Modify only if a test exposes a mismatch in `testing/evaluation/test_full_evaluation.py`
- Otherwise no code changes expected

- [ ] **Step 1: Run the full evaluation test package with the hardened benchmark files**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation -q
```

Expected: PASS, including the old evaluator tests and the new benchmark-validation tests.

- [ ] **Step 2: Run the pre-lock validation CLI against the repo benchmark artifacts**

Run:

```bash
docker compose --profile test run --rm --build service-tests python testing/evaluation/validate_benchmark_artifacts.py
```

Expected: success output from the validator and a zero exit code.

- [ ] **Step 3: Run the benchmark CLI path once to confirm the preflight gate fires before evaluation**

Run:

```bash
docker compose --profile test run --rm --build service-tests python testing/evaluation/run_evaluation.py --base-url http://gateway-api:8000 --top-k 10 --queries testing/evaluation/queries.json
```

Expected: the validator runs before the search API is queried, and the CLI either proceeds normally or stops early with a clear validation error if the artifacts are malformed.

- [ ] **Step 4: If smoke validation finds an unrelated retrieval-side regression, log it separately and do not block the benchmark lock**

Do not change retrieval weights, embeddings, or ranking parameters in response to that regression. File a separate follow-up issue instead so benchmark hardening stays unblocked.

---

## Spec Coverage Check

- Canonical judgment policy and rubric doc: **Task 1**
- `queries.json` wrapper schema and stable scene-key judgments: **Task 1**
- `audit_log.json` structure and benchmark lock history: **Task 1** and **Task 4**
- Structural validation before evaluation starts: **Task 2**
- Canonical scene-key enforcement and legacy numeric-ID rejection: **Task 2** and **Task 3**
- `run_evaluation.py` preflight gate: **Task 2**
- Targeted rerun default for caption-linked issues: **Task 4**
- Single benchmark maintainer sign-off: **Task 4**
- Retrieval-side flukes handled out of scope for this revision: **Task 5**

## Self-Review Notes

- No placeholders remain.
- The plan keeps retrieval weights, embeddings, and ranking out of scope.
- The new benchmark policy lives in `docs/metrics/`, and the query file references it explicitly.
- The validation path is separate from the evaluator path, which keeps benchmark rigor checks easy to test independently.
