# Phase 7 Evaluation Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locked local evaluation benchmark for Semedia search, expand the judged query set, add reproducible reporting and regression comparison, run the first Docker baseline, and document metric changes over time.

**Architecture:** Keep the benchmark isolated under `testing/evaluation/` so smoke tests stay unchanged. Extend the existing offline evaluator instead of introducing a parallel framework: use a manifest-backed local corpus, a richer query schema, new report sections for slices and regression comparison, then drive the full workflow through Docker commands that seed the corpus, run evaluation, save a baseline report, and append the first metrics-history entry.

**Tech Stack:** Python 3, pytest, Docker Compose, FastAPI search API, JSON datasets under `testing/evaluation/`, Markdown docs under `docs/`

---

## Execution Notes

- The user prefers not to perform git actions unless explicitly requested, so this plan does **not** include commit steps.
- Run all tests and evaluation commands through Docker.
- Keep smoke assets in `testing/smoke-assets/` unchanged.
- Keep Phase 7 docs in `Semedia/docs/` and benchmark data in `Semedia/testing/evaluation/`.

## File Structure

### New files
- `testing/evaluation/asset_manifest.json` — locked corpus manifest with one entry per local benchmark asset.
- `testing/evaluation/assets/` — image-heavy benchmark corpus committed to the repo.
- `testing/evaluation/baselines/baseline-phase7.json` — first saved baseline report produced after the corpus is seeded and evaluated.
- `testing/evaluation/test_full_evaluation.py` — integration coverage for the CLI evaluation flow and saved report generation.
- `docs/metrics/search_quality_history.md` — append-only human-readable history of benchmark runs and algorithm changes.

### Modified files
- `testing/evaluation/queries.json` — expand to 100+ judged queries with new schema fields and strict authenticity notes.
- `testing/evaluation/evaluate_search.py` — add report slicing, negative-query summaries, report comparison, and regression detection.
- `testing/evaluation/run_evaluation.py` — add JSON output, baseline comparison input, and richer console summaries.
- `testing/evaluation/seed_media.py` — allow deterministic seeding of the locked evaluation corpus without disturbing smoke fixtures.
- `testing/evaluation/test_evaluate_search.py` — add manifest validation, richer query-schema checks, new report-section tests, and regression tests.
- `docs/TASKS.md` — mark Phase 7 work complete once the baseline exists.
- `docs/plan.md` — record that Phase 7 now has a locked benchmark and baseline report.

### Files intentionally left unchanged
- `testing/smoke-assets/*` — remains the smoke corpus.
- `testing/smoke_stack.py` — Phase 7 must not change the smoke workflow.
- Production service code under `services/` — this phase measures the system; it does not change ranking or retrieval logic.

---

### Task 1: Add the locked benchmark corpus and manifest scaffolding

**Files:**
- Create: `testing/evaluation/asset_manifest.json`
- Create: `testing/evaluation/assets/`
- Modify: `testing/evaluation/test_evaluate_search.py`
- Modify: `testing/evaluation/seed_media.py`

- [ ] **Step 1: Write the failing dataset-manifest tests**

Add these tests near the bottom of `testing/evaluation/test_evaluate_search.py`:

```python
import json
from pathlib import Path


def test_asset_manifest_lists_a_large_locked_corpus():
    evaluation_dir = Path(__file__).parent
    manifest_file = evaluation_dir / "asset_manifest.json"
    assets_dir = evaluation_dir / "assets"

    assert manifest_file.exists(), "Phase 7 requires testing/evaluation/asset_manifest.json"
    assert assets_dir.exists(), "Phase 7 requires testing/evaluation/assets/"

    manifest = json.loads(manifest_file.read_text())

    assert len(manifest) >= 35
    assert sum(1 for item in manifest if item["media_type"] == "image") >= 28
    assert sum(1 for item in manifest if item["media_type"] == "video") >= 7


def test_asset_manifest_entries_reference_real_files_and_required_metadata():
    evaluation_dir = Path(__file__).parent
    manifest = json.loads((evaluation_dir / "asset_manifest.json").read_text())
    assets_dir = evaluation_dir / "assets"

    required_keys = {"asset_id", "filename", "media_type", "categories", "description", "source", "notes"}

    for item in manifest:
        assert required_keys.issubset(item)
        assert item["media_type"] in {"image", "video"}
        assert (assets_dir / item["filename"]).exists(), item["filename"]
        assert item["categories"], item["asset_id"]
        assert item["description"].strip(), item["asset_id"]
        assert item["source"].strip(), item["asset_id"]
```

- [ ] **Step 2: Run the dataset tests to verify they fail**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_evaluate_search.py -q
```

Expected: FAIL with missing-file assertions for `testing/evaluation/asset_manifest.json` and `testing/evaluation/assets/`.

- [ ] **Step 3: Add the locked corpus manifest and local assets**

Create `testing/evaluation/asset_manifest.json` with this structure and naming convention:

```json
[
  {
    "asset_id": "img-office-desk-01",
    "filename": "img-office-desk-01.jpg",
    "media_type": "image",
    "categories": ["indoor", "workspace", "desk"],
    "description": "Office desk scene with laptop, keyboard, and notebook.",
    "source": "Downloaded public-use image and stored locally for benchmark use.",
    "notes": "Positive target for office, desk, indoor, workspace, and laptop queries."
  },
  {
    "asset_id": "img-red-car-01",
    "filename": "img-red-car-01.jpg",
    "media_type": "image",
    "categories": ["vehicle", "car", "outdoor", "street", "red"],
    "description": "Red car parked on a city street in daylight.",
    "source": "Downloaded public-use image and stored locally for benchmark use.",
    "notes": "Positive target for red car; near-miss negative for blue car if no blue vehicle is present."
  },
  {
    "asset_id": "vid-dog-play-01",
    "filename": "vid-dog-play-01.mp4",
    "media_type": "video",
    "categories": ["dog", "animal", "action", "outdoor"],
    "description": "Short outdoor video of a dog running and playing.",
    "source": "Downloaded public-use video and stored locally for benchmark use.",
    "notes": "Positive target for dog, playing, running, and action queries."
  }
]
```

Populate the directory with **at least 35 local assets** using this split:
- `28` or more images named `img-<topic>-<nn>.<ext>`
- `7` or more videos named `vid-<topic>-<nn>.<ext>`

Modify `testing/evaluation/seed_media.py` so the asset directory is configurable and upload order is deterministic:

```python
def main():
    base_url = "http://gateway-api:8000"
    assets_dir = Path(
        os.environ.get("SEMEDIA_EVALUATION_ASSETS_DIR", "/app/testing/evaluation/assets")
    )

    media_files = sorted(
        list(assets_dir.glob("*.png"))
        + list(assets_dir.glob("*.jpg"))
        + list(assets_dir.glob("*.jpeg"))
        + list(assets_dir.glob("*.mp4"))
    )

    print(f"Uploading {len(media_files)} files from {assets_dir}")

    for file_path in media_files:
        print(f"\n[upload] {file_path.name}")
        result = upload_file(base_url, file_path)
        media_id = result["data"]["id"]
        detail = poll_media(base_url, media_id, timeout_seconds=300)
        print(
            json.dumps(
                {
                    "filename": file_path.name,
                    "media_id": media_id,
                    "status": detail["status"],
                    "caption": detail.get("caption"),
                }
            )
        )
```

Also add the missing import at the top of `testing/evaluation/seed_media.py`:

```python
import os
```

- [ ] **Step 4: Run the dataset tests to verify they pass**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_evaluate_search.py -q
```

Expected: PASS for the new manifest tests and the existing evaluation tests.

---

### Task 2: Expand the judged query set and lock in authenticity checks

**Files:**
- Modify: `testing/evaluation/queries.json`
- Modify: `testing/evaluation/test_evaluate_search.py`

- [ ] **Step 1: Write the failing query-schema and coverage tests**

Extend `testing/evaluation/test_evaluate_search.py` with these tests:

```python
def test_queries_dataset_has_large_balanced_phase7_coverage():
    queries_file = Path(__file__).with_name("queries.json")
    queries = load_queries(queries_file)
    judged_queries = [query for query in queries if query.get("judged")]

    assert len(judged_queries) >= 100
    assert sum(1 for query in judged_queries if query["query_type"] == "object") >= 25
    assert sum(1 for query in judged_queries if query["query_type"] == "action") >= 25
    assert sum(1 for query in judged_queries if query["query_type"] == "scene") >= 25
    assert sum(1 for query in judged_queries if not query["relevant_media_ids"] and not query["relevant_scene_ids"]) >= 20
    assert sum(1 for query in judged_queries if "near-miss" in query.get("tags", [])) >= 15


def test_phase7_queries_include_required_schema_fields():
    queries_file = Path(__file__).with_name("queries.json")
    queries = load_queries(queries_file)

    for query in queries:
        assert "media_type_target" in query, query["query_id"]
        assert query["media_type_target"] in {"image", "video", "mixed"}
        assert "difficulty" in query, query["query_id"]
        assert query["difficulty"] in {"easy", "medium", "hard"}
        assert "tags" in query, query["query_id"]
        assert isinstance(query["tags"], list), query["query_id"]
        assert query.get("notes", "").strip(), query["query_id"]
```

- [ ] **Step 2: Run the query tests to verify they fail**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_evaluate_search.py -q
```

Expected: FAIL because the current `queries.json` has only 20 entries and does not contain `media_type_target`, `difficulty`, or `tags`.

- [ ] **Step 3: Replace the Phase 1 query set with a large Phase 7 benchmark set**

Rewrite `testing/evaluation/queries.json` so every entry uses this schema:

```json
{
  "query_id": "q001",
  "query_text": "office desk",
  "query_type": "scene",
  "media_type_target": "image",
  "difficulty": "easy",
  "tags": ["positive", "workspace"],
  "judged": true,
  "relevant_media_ids": [1],
  "relevant_scene_ids": [],
  "notes": "Direct match against img-office-desk-01 after manual visual review."
}
```

Author **100 or more judged queries** with this target split:
- `25+` object queries
- `25+` action queries
- `25+` scene queries
- `20+` explicit negative queries with both relevance lists empty
- `15+` near-miss queries tagged with `"near-miss"`

Use notes that prove manual review. Example negative and near-miss entries:

```json
{
  "query_id": "q054",
  "query_text": "blue car",
  "query_type": "object",
  "media_type_target": "image",
  "difficulty": "medium",
  "tags": ["negative", "near-miss"],
  "judged": true,
  "relevant_media_ids": [],
  "relevant_scene_ids": [],
  "notes": "Manual review confirmed the benchmark contains a red car target but no blue car target."
}
```

```json
{
  "query_id": "q087",
  "query_text": "dog running in park",
  "query_type": "action",
  "media_type_target": "video",
  "difficulty": "medium",
  "tags": ["positive", "video", "action"],
  "judged": true,
  "relevant_media_ids": [31],
  "relevant_scene_ids": [66, 67],
  "notes": "Manual playback confirmed the dog-run scenes appear in the first and second outdoor segments of vid-dog-play-01."
}
```

- [ ] **Step 4: Strengthen the authenticity assertions for known edge cases**

Keep the existing ground-truth test and extend it with benchmark-specific assertions like these:

```python
def test_phase7_queries_require_notes_that_match_manual_review():
    queries_file = Path(__file__).with_name("queries.json")
    queries = load_queries(queries_file)

    for query in queries:
        if query.get("judged"):
            assert "manual" in query["notes"].lower(), query["query_id"]


def test_phase7_negative_queries_do_not_reference_relevant_ids():
    queries_file = Path(__file__).with_name("queries.json")
    queries = load_queries(queries_file)

    negative_queries = [query for query in queries if "negative" in query.get("tags", [])]

    assert negative_queries, "Phase 7 requires explicit negative queries"
    for query in negative_queries:
        assert query["relevant_media_ids"] == []
        assert query["relevant_scene_ids"] == []
```

- [ ] **Step 5: Run the tests to verify the dataset is accepted**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_evaluate_search.py -q
```

Expected: PASS with the new 100+ query benchmark and authenticity checks.

---

### Task 3: Extend the evaluation core with slices, negative summaries, and report comparison

**Files:**
- Modify: `testing/evaluation/evaluate_search.py`
- Modify: `testing/evaluation/test_evaluate_search.py`

- [ ] **Step 1: Write the failing report-shape tests**

Add these tests to `testing/evaluation/test_evaluate_search.py`:

```python
def test_run_evaluation_includes_modality_and_difficulty_breakdowns(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(json.dumps([
        {
            "query_id": "q001",
            "query_text": "office desk",
            "query_type": "scene",
            "media_type_target": "image",
            "difficulty": "easy",
            "tags": ["positive"],
            "judged": True,
            "relevant_media_ids": [1],
            "relevant_scene_ids": [],
            "notes": "Manual review confirmed the desk scene."
        },
        {
            "query_id": "q002",
            "query_text": "dog running",
            "query_type": "action",
            "media_type_target": "video",
            "difficulty": "hard",
            "tags": ["positive", "video"],
            "judged": True,
            "relevant_media_ids": [2],
            "relevant_scene_ids": [7],
            "notes": "Manual review confirmed the running scene."
        }
    ]))

    def mock_search(query_text, top_k):
        if query_text == "office desk":
            return [{"media_id": 1, "scene_id": None, "score": 0.9}]
        return [{"media_id": 2, "scene_id": 7, "score": 0.8}]

    results = run_evaluation(
        queries_file,
        mock_search,
        k=10,
        include_per_query=True,
        include_by_type=True,
        include_by_modality=True,
        include_by_difficulty=True,
        include_negative_summary=True,
    )

    assert "by_modality" in results
    assert results["by_modality"]["image"]["num_queries"] == 1
    assert results["by_modality"]["video"]["num_queries"] == 1
    assert "by_difficulty" in results
    assert results["by_difficulty"]["easy"]["num_queries"] == 1
    assert results["by_difficulty"]["hard"]["num_queries"] == 1
```

```python
def test_compare_reports_flags_metric_regressions():
    baseline_report = {
        "mean_precision@10": 0.6,
        "mean_recall@10": 0.8,
        "mean_mrr": 0.7,
        "mean_ndcg@10": 0.75,
        "negative_queries": {"false_positive_rate": 0.05},
    }
    current_report = {
        "mean_precision@10": 0.52,
        "mean_recall@10": 0.8,
        "mean_mrr": 0.7,
        "mean_ndcg@10": 0.7,
        "negative_queries": {"false_positive_rate": 0.12},
    }

    comparison = compare_reports(current_report, baseline_report, k=10, relative_drop_threshold=0.05)

    assert comparison["status"] == "regression"
    assert "mean_precision@10" in comparison["regressions"]
    assert "negative_false_positive_rate" in comparison["regressions"]
```

- [ ] **Step 2: Run the evaluation tests to verify they fail**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_evaluate_search.py -q
```

Expected: FAIL because `run_evaluation()` does not accept the new flags and `compare_reports()` does not exist.

- [ ] **Step 3: Extend `evaluate_search.py` with the new report sections**

Update the signatures and add the new helpers shown below:

```python
def summarize_group(per_query_results: list[dict], key: str, k: int) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict]] = {}
    for result in per_query_results:
        group_key = result.get(key, "unknown") or "unknown"
        grouped.setdefault(group_key, []).append(result)

    summary: dict[str, dict[str, float]] = {}
    for group_key, rows in grouped.items():
        summary[group_key] = {
            f"mean_precision@{k}": sum(r["precision@k"] for r in rows) / len(rows),
            f"mean_recall@{k}": sum(r["recall@k"] for r in rows) / len(rows),
            "mean_mrr": sum(r["mrr"] for r in rows) / len(rows),
            f"mean_ndcg@{k}": sum(r["ndcg@k"] for r in rows) / len(rows),
            "num_queries": len(rows),
        }
    return summary


def summarize_negative_queries(per_query_results: list[dict], k: int) -> dict[str, float]:
    negatives = [row for row in per_query_results if "negative" in row.get("tags", [])]
    if not negatives:
        return {"num_queries": 0, "false_positive_rate": 0.0, "mean_false_positives_per_query": 0.0}

    false_positive_counts = [len(row["retrieved_ids"]) for row in negatives]
    queries_with_false_positives = sum(1 for count in false_positive_counts if count > 0)

    return {
        "num_queries": len(negatives),
        "false_positive_rate": queries_with_false_positives / len(negatives),
        "mean_false_positives_per_query": sum(false_positive_counts) / len(negatives),
    }


def compare_reports(current_report: dict, baseline_report: dict, *, k: int, relative_drop_threshold: float = 0.05) -> dict:
    metric_names = [
        f"mean_precision@{k}",
        f"mean_recall@{k}",
        "mean_mrr",
        f"mean_ndcg@{k}",
    ]
    deltas = {}
    regressions = []

    for metric_name in metric_names:
        baseline_value = baseline_report.get(metric_name, 0.0)
        current_value = current_report.get(metric_name, 0.0)
        deltas[metric_name] = current_value - baseline_value
        if baseline_value > 0 and current_value < baseline_value * (1 - relative_drop_threshold):
            regressions.append(metric_name)

    baseline_negative_rate = baseline_report.get("negative_queries", {}).get("false_positive_rate", 0.0)
    current_negative_rate = current_report.get("negative_queries", {}).get("false_positive_rate", 0.0)
    deltas["negative_false_positive_rate"] = current_negative_rate - baseline_negative_rate
    if current_negative_rate > baseline_negative_rate + 0.05:
        regressions.append("negative_false_positive_rate")

    return {
        "status": "regression" if regressions else "ok",
        "regressions": regressions,
        "deltas": deltas,
    }
```

Update `run_evaluation()` to populate the richer per-query rows and optional sections:

```python
def run_evaluation(
    queries_file: Path,
    search_fn: Callable[[str, int], list[dict]],
    k: int = 10,
    *,
    include_per_query: bool = False,
    include_by_type: bool = False,
    include_by_modality: bool = False,
    include_by_difficulty: bool = False,
    include_negative_summary: bool = False,
) -> dict:
    ...
    if include_per_query:
        per_query_results.append(
            {
                "query_id": query["query_id"],
                "query_text": query["query_text"],
                "query_type": query.get("query_type", "unknown"),
                "media_type_target": query.get("media_type_target", "mixed"),
                "difficulty": query.get("difficulty", "unknown"),
                "tags": query.get("tags", []),
                "precision@k": metrics[f"precision@{k}"],
                "recall@k": metrics[f"recall@{k}"],
                "mrr": metrics["mrr"],
                "ndcg@k": metrics[f"ndcg@{k}"],
                "retrieved_ids": retrieved_ids[:k],
            }
        )
    ...
    if include_by_type:
        result["by_type"] = summarize_group(per_query_results, "query_type", k)
    if include_by_modality:
        result["by_modality"] = summarize_group(per_query_results, "media_type_target", k)
    if include_by_difficulty:
        result["by_difficulty"] = summarize_group(per_query_results, "difficulty", k)
    if include_negative_summary:
        result["negative_queries"] = summarize_negative_queries(per_query_results, k)
```

- [ ] **Step 4: Run the evaluation tests to verify the richer reports pass**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_evaluate_search.py -q
```

Expected: PASS for the new report-section tests and the earlier dataset tests.

---

### Task 4: Extend the CLI evaluation runner and add end-to-end integration coverage

**Files:**
- Modify: `testing/evaluation/run_evaluation.py`
- Create: `testing/evaluation/test_full_evaluation.py`

- [ ] **Step 1: Write the failing integration test for saved reports and comparison output**

Create `testing/evaluation/test_full_evaluation.py` with this test:

```python
from __future__ import annotations

import json
from pathlib import Path

from testing.evaluation.evaluate_search import compare_reports, run_evaluation


def test_full_evaluation_report_can_be_saved_and_compared(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "office desk",
                    "query_type": "scene",
                    "media_type_target": "image",
                    "difficulty": "easy",
                    "tags": ["positive"],
                    "judged": True,
                    "relevant_media_ids": [1],
                    "relevant_scene_ids": [],
                    "notes": "Manual review confirmed the desk scene.",
                },
                {
                    "query_id": "q002",
                    "query_text": "blue car",
                    "query_type": "object",
                    "media_type_target": "image",
                    "difficulty": "medium",
                    "tags": ["negative", "near-miss"],
                    "judged": True,
                    "relevant_media_ids": [],
                    "relevant_scene_ids": [],
                    "notes": "Manual review confirmed there is no blue car target.",
                },
            ]
        )
    )

    def search_fn(query_text: str, top_k: int) -> list[dict]:
        if query_text == "office desk":
            return [{"media_id": 1, "scene_id": None, "score": 0.9}]
        return [{"media_id": 9, "scene_id": None, "score": 0.2}]

    current_report = run_evaluation(
        queries_file,
        search_fn,
        k=10,
        include_per_query=True,
        include_by_type=True,
        include_by_modality=True,
        include_by_difficulty=True,
        include_negative_summary=True,
    )

    baseline_report = {
        "mean_precision@10": 0.2,
        "mean_recall@10": 0.5,
        "mean_mrr": 0.5,
        "mean_ndcg@10": 0.5,
        "negative_queries": {"false_positive_rate": 1.0},
    }

    comparison = compare_reports(current_report, baseline_report, k=10)

    output_file = tmp_path / "report.json"
    payload = {"report": current_report, "comparison": comparison}
    output_file.write_text(json.dumps(payload, indent=2))

    saved = json.loads(output_file.read_text())
    assert saved["report"]["num_queries"] == 2
    assert saved["report"]["negative_queries"]["num_queries"] == 1
    assert saved["comparison"]["status"] == "ok"
```

- [ ] **Step 2: Run the integration test to verify it fails**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_full_evaluation.py -q
```

Expected: FAIL until the runner can emit the richer report payload and comparison metadata.

- [ ] **Step 3: Extend `run_evaluation.py` with report output and comparison flags**

Modify `testing/evaluation/run_evaluation.py` so the CLI accepts structured output options:

```python
parser.add_argument("--output", default=None, help="Write the evaluation report JSON to this path")
parser.add_argument("--compare-to", default=None, help="Path to a saved baseline report JSON")
parser.add_argument(
    "--relative-drop-threshold",
    type=float,
    default=0.05,
    help="Relative metric drop that should be flagged as a regression",
)
```

Call `run_evaluation()` with all report sections enabled:

```python
results = run_evaluation(
    queries_file,
    search_fn,
    k=args.top_k,
    include_per_query=True,
    include_by_type=True,
    include_by_modality=True,
    include_by_difficulty=True,
    include_negative_summary=True,
)
```

Add output-payload handling after evaluation:

```python
payload = {"report": results}

if args.compare_to:
    baseline_payload = json.loads(Path(args.compare_to).read_text())
    baseline_report = baseline_payload.get("report", baseline_payload)
    comparison = compare_reports(
        results,
        baseline_report,
        k=args.top_k,
        relative_drop_threshold=args.relative_drop_threshold,
    )
    payload["comparison"] = comparison
    print(f"Comparison status: {comparison['status']}")

if args.output:
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))
    print(f"Saved evaluation report to {output_path}")
```

Also print the new sections to stdout when present:

```python
if "negative_queries" in results:
    negatives = results["negative_queries"]
    print("\nNegative-query Summary")
    print("=" * 80)
    print(f"Queries evaluated: {negatives['num_queries']}")
    print(f"False positive rate: {negatives['false_positive_rate']:.4f}")
    print(f"Mean false positives/query: {negatives['mean_false_positives_per_query']:.4f}")
```

- [ ] **Step 4: Run the focused integration test and then the whole evaluation suite**

Run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation/test_full_evaluation.py -q
```

Expected: PASS.

Then run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation -q
```

Expected: PASS for the entire evaluation test package.

---

### Task 5: Add metrics-history documentation and update project tracking docs

**Files:**
- Create: `docs/metrics/search_quality_history.md`
- Modify: `docs/TASKS.md`
- Modify: `docs/plan.md`

- [ ] **Step 1: Create the history document with the required entry template**

Create `docs/metrics/search_quality_history.md` with this initial content:

```md
# Search Quality Metrics History

This file records every accepted evaluation run after a search algorithm or benchmark change.

## Entry Template

### YYYY-MM-DD — Revision label
- **Revision:** `<revision-label>`
- **Corpus:** `<corpus-version>`
- **Queries:** `<query-version>`
- **What changed:**
  - `<short change summary>`
- **Metrics:**
  - Precision@10: `<value>`
  - Recall@10: `<value>`
  - MRR: `<value>`
  - NDCG@10: `<value>`
- **By type:**
  - Objects: `<summary>`
  - Actions: `<summary>`
  - Scenes: `<summary>`
- **Notable observations:**
  - `<important win, regression, or ambiguity>`
- **Decision:** `<accepted / tune further / revert>`
```

- [ ] **Step 2: Update the planning docs to reflect the real Phase 7 deliverables**

In `docs/TASKS.md`, expand the Phase 7 checklist to mention:

```md
- [ ] 7.1 Finalize judged dataset
  - [ ] Add `testing/evaluation/asset_manifest.json`
  - [ ] Commit 35+ locked local evaluation assets under `testing/evaluation/assets/`
  - [ ] Expand `testing/evaluation/queries.json` to 100+ judged queries
  - [ ] Double-check authenticity by comparing the actual media content against every judged query
```

In `docs/plan.md`, update the Phase 7 deliverables block to mention:

```md
### Deliverables
- `testing/evaluation/asset_manifest.json`
- locked benchmark corpus under `testing/evaluation/assets/`
- `testing/evaluation/baselines/baseline-phase7.json`
- `docs/metrics/search_quality_history.md`
- reproducible metric reports and comparison flow
```

- [ ] **Step 3: Verify the docs exist and read cleanly**

Run:

```bash
docker compose --profile test run --rm --build service-tests python - <<'PY'
from pathlib import Path
for path in [
    Path('docs/metrics/search_quality_history.md'),
    Path('docs/TASKS.md'),
    Path('docs/plan.md'),
]:
    text = path.read_text()
    assert text.strip(), path
print('docs-ok')
PY
```

Expected: `docs-ok`

---

### Task 6: Seed the locked corpus, run the Docker baseline, and document it

**Files:**
- Modify: `testing/evaluation/baselines/baseline-phase7.json`
- Modify: `docs/metrics/search_quality_history.md`
- Modify: `docs/TASKS.md`
- Modify: `docs/plan.md`

- [ ] **Step 1: Reset the disposable evaluation stack and start the services**

Run:

```bash
docker compose down -v && docker compose up --build -d gateway-api
```

Expected: containers for `db`, `media-worker`, `search-api`, and `gateway-api` come up cleanly with a fresh database and storage volume.

- [ ] **Step 2: Seed the locked evaluation corpus into the fresh stack**

Run:

```bash
docker compose exec gateway-api python testing/evaluation/seed_media.py
```

Expected: one `[upload] <filename>` block per asset, followed by JSON lines showing deterministic `media_id` assignments and `status` of `completed`.

- [ ] **Step 3: Run the first baseline evaluation and save the JSON report**

Run:

```bash
docker compose exec gateway-api python testing/evaluation/run_evaluation.py \
  --base-url http://127.0.0.1:8000 \
  --top-k 10 \
  --output testing/evaluation/baselines/baseline-phase7.json
```

Expected:
- Console output prints overall metrics, by-type metrics, negative-query summary, and the saved-report path.
- `testing/evaluation/baselines/baseline-phase7.json` exists and contains a top-level `report` object.

- [ ] **Step 4: Append the first accepted metrics-history entry using the saved report**

Open `testing/evaluation/baselines/baseline-phase7.json`, copy the actual metrics, and append an entry like this to `docs/metrics/search_quality_history.md`:

```md
## 2026-05-02 — baseline-phase7

- **Revision:** `baseline-phase7`
- **Corpus:** `eval-v1`
- **Queries:** `queries-v1`
- **What changed:**
  - Added the locked Phase 7 benchmark corpus under `testing/evaluation/assets/`
  - Replaced the Phase 1 query file with a 100+ judged benchmark set
  - Added modality slices, difficulty slices, negative-query summaries, and saved report output
- **Metrics:**
  - Precision@10: `<copy from baseline-phase7.json>`
  - Recall@10: `<copy from baseline-phase7.json>`
  - MRR: `<copy from baseline-phase7.json>`
  - NDCG@10: `<copy from baseline-phase7.json>`
- **By type:**
  - Objects: `<copy from report.by_type.object>`
  - Actions: `<copy from report.by_type.action>`
  - Scenes: `<copy from report.by_type.scene>`
- **Notable observations:**
  - `<document the strongest and weakest category>`
  - `<document the negative-query false-positive rate>`
  - `<document any queries that still look suspicious after manual review>`
- **Decision:** `accepted`
```

- [ ] **Step 5: Mark Phase 7 complete in the project docs and rerun the evaluation tests**

Update the remaining Phase 7 checklist items in `docs/TASKS.md` and status lines in `docs/plan.md`, then run:

```bash
docker compose --profile test run --rm --build service-tests pytest testing/evaluation -q
```

Expected: PASS.

- [ ] **Step 6: Sanity-check the two output artifacts**

Run:

```bash
docker compose --profile test run --rm --build service-tests python - <<'PY'
import json
from pathlib import Path
baseline = json.loads(Path('testing/evaluation/baselines/baseline-phase7.json').read_text())
history = Path('docs/metrics/search_quality_history.md').read_text()
assert 'report' in baseline
assert 'baseline-phase7' in history
print('baseline-artifacts-ok')
PY
```

Expected: `baseline-artifacts-ok`

---

## Spec Coverage Check

- Locked local corpus under `testing/evaluation/assets/`: **Task 1**
- `asset_manifest.json` with audit metadata: **Task 1**
- 100+ judged queries with new schema and balanced coverage: **Task 2**
- Strict manual authenticity verification: **Task 2** and **Task 6**
- Richer evaluator sections (`by_type`, `by_modality`, `by_difficulty`, `negative_queries`): **Task 3**
- Baseline comparison and regression detection: **Task 3** and **Task 4**
- Saved baseline report JSON: **Task 4** and **Task 6**
- Metrics-history document: **Task 5** and **Task 6**
- Docker baseline run and documented first entry: **Task 6**
- Docs updates in `docs/TASKS.md` and `docs/plan.md`: **Task 5** and **Task 6**

## Self-Review Notes

- No placeholders remain for file paths, commands, or required report sections.
- The plan keeps smoke assets and production ranking logic unchanged.
- The only intentionally manual step is the media-authenticity review, and that manual work is enforced by query notes, negative-query tests, and the baseline-history entry.
