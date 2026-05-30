from __future__ import annotations

import json
from pathlib import Path

import pytest

from testing.evaluation.evaluate_search import (
    compare_reports,
    compute_metrics,
    load_queries,
    run_evaluation,
)
from testing.evaluation.benchmark_validation import validate_scene_key


def test_load_queries_reads_json_file(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            {
                "judgment_policy": {
                    "path": "docs/metrics/evaluation_benchmark_rubric.md",
                    "version": "2026-05-11",
                },
                "queries": [
                    {
                        "query_id": "q001",
                        "query_text": "cat",
                        "query_type": "object",
                        "judged": True,
                        "relevant_media_ids": [1, 2],
                        "relevant_scene_ids": ["scene:vid-cat-01.webm:1"],
                        "media_type_target": "image",
                        "difficulty": "easy",
                        "tags": ["test"],
                        "notes": "Test query",
                    }
                ],
            }
        )
    )

    queries = load_queries(queries_file)

    assert len(queries) == 1
    assert queries[0]["query_id"] == "q001"
    assert queries[0]["query_text"] == "cat"
    assert queries[0]["relevant_media_ids"] == [1, 2]
    assert queries[0]["relevant_scene_ids"] == ["scene:vid-cat-01.webm:1"]
    assert queries[0]["judged"] is True


def test_compute_metrics_calculates_precision_at_k():
    relevant_ids = {1, 2, 3}
    retrieved_ids = [1, 4, 2, 5, 6, 7, 8, 9, 10, 11]

    metrics = compute_metrics(relevant_ids, retrieved_ids, k=10)

    # 2 relevant in top 10 out of 3 total relevant
    assert metrics["precision@10"] == 0.2  # 2/10
    assert metrics["recall@10"] == pytest.approx(0.6667, rel=1e-3)  # 2/3


def test_compute_metrics_calculates_mrr():
    relevant_ids = {2, 5}
    retrieved_ids = [1, 2, 3, 4, 5]

    metrics = compute_metrics(relevant_ids, retrieved_ids, k=10)

    # First relevant at rank 2 (index 1)
    assert metrics["mrr"] == 0.5  # 1/2


def test_compute_metrics_calculates_ndcg():
    relevant_ids = {1, 2, 3}
    retrieved_ids = [1, 4, 2, 5, 3]

    metrics = compute_metrics(relevant_ids, retrieved_ids, k=5)

    # DCG: 1/log2(2) + 1/log2(4) + 1/log2(6)
    # IDCG: 1/log2(2) + 1/log2(3) + 1/log2(4)
    assert "ndcg@5" in metrics
    assert 0 < metrics["ndcg@5"] <= 1


def test_compute_metrics_deduplicates_retrieved_ids_preserving_order():
    metrics = compute_metrics({"media:1", "media:2"}, ["media:1", "media:1", "media:3", "media:2"], k=3)

    assert metrics["precision@3"] == 2 / 3
    assert metrics["recall@3"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["ndcg@3"] < 1.0


def test_compute_metrics_handles_no_relevant_results():
    relevant_ids = {1, 2}
    retrieved_ids = [3, 4, 5]

    metrics = compute_metrics(relevant_ids, retrieved_ids, k=10)

    assert metrics["precision@10"] == 0.0
    assert metrics["recall@10"] == 0.0
    assert metrics["mrr"] == 0.0
    assert metrics["ndcg@10"] == 0.0


def test_compute_metrics_handles_empty_retrieved():
    relevant_ids = {1, 2}
    retrieved_ids = []

    metrics = compute_metrics(relevant_ids, retrieved_ids, k=10)

    assert metrics["precision@10"] == 0.0
    assert metrics["recall@10"] == 0.0
    assert metrics["mrr"] == 0.0
    assert metrics["ndcg@10"] == 0.0


def test_run_evaluation_returns_aggregated_metrics(tmp_path, monkeypatch):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "cat",
                    "query_type": "object",
                    "relevant_media_ids": [1],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
                {
                    "query_id": "q002",
                    "query_text": "dog",
                    "query_type": "object",
                    "relevant_media_ids": [2],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
            ]
        )
    )

    def mock_search(query_text, top_k):
        if query_text == "cat":
            return [
                {"media_id": 1, "scene_id": None, "score": 95.0},
                {"media_id": 3, "scene_id": None, "score": 80.0},
            ]
        else:
            return [
                {"media_id": 4, "scene_id": None, "score": 90.0},
                {"media_id": 2, "scene_id": None, "score": 85.0},
            ]

    results = run_evaluation(queries_file, mock_search, k=10)

    assert "mean_precision@10" in results
    assert "mean_recall@10" in results
    assert "mean_mrr" in results
    assert "mean_ndcg@10" in results
    assert results["num_queries"] == 2


def test_run_evaluation_skips_unjudged_queries_and_matches_scene_ids(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            {
                "judgment_policy": {
                    "path": "docs/metrics/evaluation_benchmark_rubric.md",
                    "version": "2026-05-11",
                },
                "queries": [
                    {
                        "query_id": "q001",
                        "query_text": "cat",
                        "query_type": "object",
                        "judged": True,
                        "relevant_media_ids": [1],
                        "relevant_scene_ids": [],
                        "media_type_target": "image",
                        "difficulty": "easy",
                        "tags": ["positive"],
                        "notes": "",
                    },
                    {
                        "query_id": "q002",
                        "query_text": "night scene",
                        "query_type": "scene",
                        "judged": True,
                        "relevant_media_ids": [],
                        "relevant_scene_ids": ["scene:vid-night-city-01.webm:2"],
                        "media_type_target": "video",
                        "difficulty": "medium",
                        "tags": ["positive"],
                        "notes": "",
                    },
                    {
                        "query_id": "q003",
                        "query_text": "unused",
                        "query_type": "scene",
                        "judged": False,
                        "relevant_media_ids": [],
                        "relevant_scene_ids": [],
                        "media_type_target": "video",
                        "difficulty": "easy",
                        "tags": ["negative"],
                        "notes": "",
                    },
                ],
            }
        )
    )

    def mock_search(query_text, top_k):
        if query_text == "cat":
            return [{"media_id": 1, "scene_id": None, "score": 99.0}]
        if query_text == "night scene":
            return [{"media_id": 10, "scene_id": 2, "scene_key": "scene:vid-night-city-01.webm:2", "score": 88.0}]
        return [{"media_id": 999, "scene_id": None, "score": 10.0}]

    results = run_evaluation(queries_file, mock_search, k=10)

    assert results["num_queries"] == 2
    assert results["mean_recall@10"] == 1.0


def test_run_evaluation_includes_per_query_results_when_requested(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            {
                "judgment_policy": {
                    "path": "docs/metrics/evaluation_benchmark_rubric.md",
                    "version": "2026-05-11",
                },
                "queries": [
                    {
                        "query_id": "q001",
                        "query_text": "cat",
                        "query_type": "object",
                        "judged": True,
                        "relevant_media_ids": [1],
                        "relevant_scene_ids": [],
                        "media_type_target": "image",
                        "difficulty": "easy",
                        "tags": ["positive"],
                        "notes": "",
                    },
                    {
                        "query_id": "q002",
                        "query_text": "dog",
                        "query_type": "action",
                        "judged": True,
                        "relevant_media_ids": [2],
                        "relevant_scene_ids": [],
                        "media_type_target": "image",
                        "difficulty": "easy",
                        "tags": ["positive"],
                        "notes": "",
                    },
                ],
            }
        )
    )

    def mock_search(query_text, top_k):
        if query_text == "cat":
            return [{"media_id": 1, "scene_id": None, "score": 95.0}]
        else:
            return [{"media_id": 2, "scene_id": None, "score": 85.0}]

    results = run_evaluation(queries_file, mock_search, k=10, include_per_query=True)

    assert "per_query" in results
    assert len(results["per_query"]) == 2
    assert results["per_query"][0]["query_id"] == "q001"
    assert results["per_query"][0]["query_text"] == "cat"
    assert results["per_query"][0]["query_type"] == "object"
    assert "precision@k" in results["per_query"][0]
    assert "recall@k" in results["per_query"][0]
    assert "mrr" in results["per_query"][0]
    assert "ndcg@k" in results["per_query"][0]
    assert "retrieved_ids" in results["per_query"][0]


def test_run_evaluation_includes_by_type_metrics_when_requested(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "cat",
                    "query_type": "object",
                    "relevant_media_ids": [1],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
                {
                    "query_id": "q002",
                    "query_text": "sunset",
                    "query_type": "scene",
                    "relevant_media_ids": [2],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
                {
                    "query_id": "q003",
                    "query_text": "running",
                    "query_type": "action",
                    "relevant_media_ids": [3],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
            ]
        )
    )

    def mock_search(query_text, top_k):
        return [{"media_id": 1, "scene_id": None, "score": 90.0}]

    results = run_evaluation(queries_file, mock_search, k=10, include_per_query=True, include_by_type=True)

    assert "by_type" in results
    assert "object" in results["by_type"]
    assert "scene" in results["by_type"]
    assert "action" in results["by_type"]
    assert results["by_type"]["object"]["num_queries"] == 1
    assert results["by_type"]["scene"]["num_queries"] == 1
    assert results["by_type"]["action"]["num_queries"] == 1
    assert "mean_precision@10" in results["by_type"]["object"]
    assert "mean_recall@10" in results["by_type"]["object"]


def test_run_evaluation_per_query_preserves_retrieved_ids(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "cat",
                    "query_type": "object",
                    "relevant_media_ids": [1],
                    "relevant_scene_ids": [],
                    "notes": "",
                }
            ]
        )
    )

    def mock_search(query_text, top_k):
        return [
            {"media_id": 1, "scene_id": None, "score": 95.0},
            {"media_id": 10, "scene_id": 5, "score": 80.0},
        ]

    results = run_evaluation(queries_file, mock_search, k=10, include_per_query=True)

    assert results["per_query"][0]["retrieved_ids"] == ["media:1", "scene:5"]


def test_run_evaluation_prefers_stable_scene_keys_when_present(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "train passing",
                    "query_type": "action",
                    "relevant_media_ids": [],
                    "relevant_scene_ids": ["scene:vid-train-passing-01.webm:1"],
                    "notes": "",
                }
            ]
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


def test_run_evaluation_backward_compatible_without_flags(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "cat",
                    "query_type": "object",
                    "relevant_media_ids": [1],
                    "relevant_scene_ids": [],
                    "notes": "",
                }
            ]
        )
    )

    def mock_search(query_text, top_k):
        return [{"media_id": 1, "scene_id": None, "score": 95.0}]

    results = run_evaluation(queries_file, mock_search, k=10)

    assert "per_query" not in results
    assert "by_type" not in results
    assert "mean_precision@10" in results
    assert "num_queries" in results



def test_run_evaluation_includes_modality_and_difficulty_breakdowns(tmp_path):
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
                    "query_text": "dog running",
                    "query_type": "action",
                    "media_type_target": "video",
                    "difficulty": "hard",
                    "tags": ["positive", "video"],
                    "judged": True,
                    "relevant_media_ids": [2],
                    "relevant_scene_ids": ["scene:vid-dog-agility-01.webm:0"],
                    "notes": "Manual review confirmed the running scene.",
                },
            ]
        )
    )

    def mock_search(query_text, top_k):
        if query_text == "office desk":
            return [{"media_id": 1, "scene_id": None, "score": 0.9}]
        return [{"media_id": 2, "scene_id": 7, "scene_key": "scene:vid-dog-agility-01.webm:0", "score": 0.8}]

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
    assert "negative_queries" in results
    assert results["negative_queries"]["num_queries"] == 0


def test_run_evaluation_deduplicates_per_query_retrieved_ids_for_negative_summary(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "no matching asset",
                    "query_type": "object",
                    "judged": True,
                    "relevant_media_ids": [],
                    "relevant_scene_ids": [],
                    "tags": ["negative"],
                    "notes": "Negative query for duplicate handling.",
                }
            ]
        )
    )

    def mock_search(query_text, top_k):
        return [
            {"media_id": 1, "scene_id": None, "score": 0.9},
            {"media_id": 1, "scene_id": None, "score": 0.8},
        ]

    results = run_evaluation(queries_file, mock_search, k=10, include_per_query=True, include_negative_summary=True)

    assert results["per_query"][0]["retrieved_ids"] == ["media:1"]
    assert results["negative_queries"]["mean_false_positives_per_query"] == 1.0


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



def _load_phase7_queries() -> list[dict]:
    queries_file = Path(__file__).with_name("queries.json")
    return load_queries(queries_file)


def _load_phase7_manifest() -> list[dict]:
    manifest_file = Path(__file__).with_name("asset_manifest.json")
    return json.loads(manifest_file.read_text())


def test_queries_dataset_meets_phase7_task2_coverage_requirements():
    queries = _load_phase7_queries()
    judged_queries = [query for query in queries if query.get("judged")]
    judged_by_type = {
        query_type: [query for query in judged_queries if query.get("query_type") == query_type]
        for query_type in {"object", "action", "scene"}
    }
    explicit_negative_queries = [
        query
        for query in judged_queries
        if not query.get("relevant_media_ids") and not query.get("relevant_scene_ids")
    ]
    near_miss_queries = [
        query
        for query in judged_queries
        if "near-miss" in query.get("tags", [])
    ]

    assert len(judged_queries) >= 100, "Phase 7 Task 2 requires at least 100 judged queries"
    assert len(judged_by_type["object"]) >= 25, "Need at least 25 object queries"
    assert len(judged_by_type["action"]) >= 25, "Need at least 25 action queries"
    assert len(judged_by_type["scene"]) >= 25, "Need at least 25 scene queries"
    assert len(explicit_negative_queries) >= 20, "Need at least 20 explicit negative queries"
    assert len(near_miss_queries) >= 15, "Need at least 15 near-miss queries"
    assert len({query["query_id"] for query in queries}) == len(queries), "query_id values must be unique"


def test_run_evaluation_includes_explicitly_judged_queries_with_no_relevant_items(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "forest",
                    "query_type": "scene",
                    "judged": True,
                    "relevant_media_ids": [],
                    "relevant_scene_ids": [],
                    "media_type_target": "image",
                    "difficulty": "hard",
                    "tags": ["negative"],
                    "notes": "Manual review: no relevant forest content exists in this corpus.",
                }
            ]
        )
    )

    def mock_search(query_text, top_k):
        return [{"media_id": 99, "scene_id": None, "score": 50.0}]

    results = run_evaluation(queries_file, mock_search, k=10)

    assert results["num_queries"] == 0  # negatives excluded from the positive means
    assert results["num_negative_queries"] == 1  # but still recognized as a judged negative
    assert results["mean_precision@10"] == 0.0
    assert results["mean_recall@10"] == 0.0
    assert results["mean_mrr"] == 0.0
    assert results["mean_ndcg@10"] == 0.0


def test_queries_dataset_uses_phase7_task2_schema_and_manual_notes():
    queries = _load_phase7_queries()
    judged_queries = [query for query in queries if query.get("judged")]
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

    for query in judged_queries:
        assert required_fields.issubset(query), f"Missing required field(s) in {query.get('query_id')}"
        assert query["query_id"].strip(), "query_id must be non-empty"
        assert query["query_text"].strip(), f"query_text must be non-empty for {query['query_id']}"
        assert query["query_type"] in {"object", "action", "scene"}
        assert query["media_type_target"] in {"image", "video", "mixed"}
        assert query["difficulty"] in {"easy", "medium", "hard"}
        assert isinstance(query["tags"], list), f"tags must be a list for {query['query_id']}"
        assert all(isinstance(tag, str) and tag.strip() for tag in query["tags"]), (
            f"tags must contain non-empty strings for {query['query_id']}"
        )
        assert query["notes"].strip(), f"notes must be non-empty for {query['query_id']}"
        assert "manual" in query["notes"].lower(), (
            f"notes must show manual review for {query['query_id']}"
        )


def test_queries_dataset_ground_truth_matches_manifest_and_negative_queries_stay_generic():
    queries = _load_phase7_queries()
    manifest = _load_phase7_manifest()
    judged_queries = [query for query in queries if query.get("judged")]
    corpus_size = len(manifest)
    manifest_asset_tokens = {
        item["asset_id"].lower() for item in manifest
    } | {
        item["filename"].lower() for item in manifest
    }

    for query in judged_queries:
        relevant_media_ids = query.get("relevant_media_ids", [])
        relevant_scene_ids = query.get("relevant_scene_ids", [])

        assert len(relevant_media_ids) == len(set(relevant_media_ids)), (
            f"Duplicate media ids found in {query['query_id']}"
        )
        assert len(relevant_scene_ids) == len(set(relevant_scene_ids)), (
            f"Duplicate scene ids found in {query['query_id']}"
        )

        for media_id in relevant_media_ids:
            assert 1 <= media_id <= corpus_size, (
                f"Query {query['query_id']} references media_id={media_id}, "
                f"but the corpus only has {corpus_size} assets (1-indexed)."
            )

        for scene_id in relevant_scene_ids:
            validate_scene_key(scene_id)
            _, filename, _ = scene_id.split(":")
            assert filename in manifest_asset_tokens, (
                f"Query {query['query_id']} references unknown scene filename {filename}"
            )

        if relevant_media_ids:
            relevant_media_types = {manifest[media_id - 1]["media_type"] for media_id in relevant_media_ids}
            if query["media_type_target"] == "image":
                assert relevant_media_types == {"image"}, (
                    f"Query {query['query_id']} targets images but references non-image media ids"
                )
            elif query["media_type_target"] == "video":
                assert relevant_media_types == {"video"}, (
                    f"Query {query['query_id']} targets videos but references non-video media ids"
                )
            elif query["media_type_target"] == "mixed":
                assert len(relevant_media_types) >= 1

        if not relevant_media_ids and not relevant_scene_ids:
            negative_notes = query["notes"].lower()
            assert "media:" not in negative_notes, (
                f"Negative query {query['query_id']} should not reference media ids in notes"
            )
            assert "scene:" not in negative_notes, (
                f"Negative query {query['query_id']} should not reference scene ids in notes"
            )
            for token in manifest_asset_tokens:
                assert token not in negative_notes, (
                    f"Negative query {query['query_id']} should not reference asset identifiers in notes"
                )

        if "near-miss" in query["tags"]:
            assert query["difficulty"] in {"medium", "hard"}, (
                f"Near-miss query {query['query_id']} should not be marked easy"
            )
            assert query["notes"].strip(), f"Near-miss query {query['query_id']} must explain the distinction"

        if relevant_media_ids or relevant_scene_ids:
            assert query["notes"].strip(), f"Positive query {query['query_id']} must explain manual judgment"
            assert query["query_text"].strip().lower() != "negative", "Query text must be descriptive"

    assert len(judged_queries) >= 100, "Phase 7 Task 2 requires at least 100 judged queries"


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



def test_compute_metrics_caps_mrr_at_k():
    relevant_ids = {"media:99"}
    retrieved_ids = [f"media:{i}" for i in range(11)] + ["media:99"]  # first relevant at rank 12

    metrics = compute_metrics(relevant_ids, retrieved_ids, k=10)

    assert metrics["mrr"] == 0.0


def test_run_evaluation_excludes_negatives_from_means_and_slices(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q1",
                    "query_text": "cat",
                    "query_type": "object",
                    "media_type_target": "image",
                    "difficulty": "easy",
                    "tags": ["positive"],
                    "judged": True,
                    "relevant_media_ids": [1],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
                {
                    "query_id": "q2",
                    "query_text": "elephant",
                    "query_type": "object",
                    "media_type_target": "image",
                    "difficulty": "hard",
                    "tags": ["negative"],
                    "judged": True,
                    "relevant_media_ids": [],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
            ]
        )
    )

    def mock_search(query_text, top_k):
        if query_text == "cat":
            return [{"media_id": 1, "scene_id": None, "score": 0.9}]
        return [{"media_id": 7, "scene_id": None, "score": 0.9}]

    results = run_evaluation(
        queries_file,
        mock_search,
        k=10,
        include_by_difficulty=True,
        include_negative_summary=True,
    )

    assert results["num_queries"] == 1  # positives only
    assert results["num_negative_queries"] == 1
    assert results["mean_recall@10"] == 1.0  # negative no longer drags the mean
    assert "hard" not in results["by_difficulty"]  # negative-only 'hard' excluded from slices
    assert results["by_difficulty"]["easy"]["num_queries"] == 1
    assert results["negative_queries"]["num_queries"] == 1
    assert results["negative_queries"]["false_positive_rate"] == 1.0


def test_negative_summary_is_threshold_aware(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q1",
                    "query_text": "elephant",
                    "query_type": "object",
                    "media_type_target": "image",
                    "difficulty": "hard",
                    "tags": ["negative"],
                    "judged": True,
                    "relevant_media_ids": [],
                    "relevant_scene_ids": [],
                    "notes": "",
                }
            ]
        )
    )

    def mock_search(query_text, top_k):
        return [{"media_id": 5, "scene_id": None, "score": 0.3}]  # weak, low-confidence hit

    base = run_evaluation(queries_file, mock_search, k=10, include_negative_summary=True)
    assert base["negative_queries"]["false_positive_rate"] == 1.0  # any returned hit counts

    thresholded = run_evaluation(
        queries_file, mock_search, k=10, include_negative_summary=True, negative_score_threshold=0.5
    )
    assert thresholded["negative_queries"]["false_positive_rate"] == 0.0  # 0.3 < 0.5
    assert thresholded["negative_queries"]["mean_false_positives_per_query"] == 0.0
    assert thresholded["negative_queries"]["score_threshold"] == 0.5
