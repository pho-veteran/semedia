from __future__ import annotations

import json
from pathlib import Path

import pytest

from testing.evaluation.evaluate_search import (
    compute_metrics,
    load_queries,
    run_evaluation,
)


def test_load_queries_reads_json_file(tmp_path):
    queries_file = tmp_path / "queries.json"
    queries_file.write_text(
        json.dumps(
            [
                {
                    "query_id": "q001",
                    "query_text": "cat",
                    "query_type": "object",
                    "relevant_media_ids": [1, 2],
                    "relevant_scene_ids": [10, 11],
                    "notes": "Test query",
                }
            ]
        )
    )

    queries = load_queries(queries_file)

    assert len(queries) == 1
    assert queries[0]["query_id"] == "q001"
    assert queries[0]["query_text"] == "cat"
    assert queries[0]["relevant_media_ids"] == [1, 2]
    assert queries[0]["relevant_scene_ids"] == [10, 11]


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
                    "query_text": "night scene",
                    "query_type": "scene",
                    "relevant_media_ids": [],
                    "relevant_scene_ids": [2],
                    "notes": "",
                },
                {
                    "query_id": "q003",
                    "query_text": "unused",
                    "query_type": "scene",
                    "relevant_media_ids": [],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
            ]
        )
    )

    def mock_search(query_text, top_k):
        if query_text == "cat":
            return [{"media_id": 1, "scene_id": None, "score": 99.0}]
        if query_text == "night scene":
            return [{"media_id": 10, "scene_id": 2, "score": 88.0}]
        return [{"media_id": 999, "scene_id": None, "score": 10.0}]

    results = run_evaluation(queries_file, mock_search, k=10)

    assert results["num_queries"] == 2
    assert results["mean_recall@10"] == 1.0


def test_run_evaluation_includes_per_query_results_when_requested(tmp_path):
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
                    "query_type": "action",
                    "relevant_media_ids": [2],
                    "relevant_scene_ids": [],
                    "notes": "",
                },
            ]
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



def test_queries_dataset_has_broad_judged_coverage():
    queries_file = Path(__file__).with_name("queries.json")
    queries = load_queries(queries_file)

    judged_queries = [
        query
        for query in queries
        if query.get("judged")
    ]

    judged_by_type = {
        query_type: [
            query for query in judged_queries if query.get("query_type") == query_type
        ]
        for query_type in {"object", "action", "scene"}
    }

    assert len(judged_queries) >= 15
    assert len(judged_by_type["object"]) >= 4
    assert len(judged_by_type["action"]) >= 4
    assert len(judged_by_type["scene"]) >= 4



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
                    "notes": "No relevant forest content exists in this corpus.",
                }
            ]
        )
    )

    def mock_search(query_text, top_k):
        return [{"media_id": 99, "scene_id": None, "score": 50.0}]

    results = run_evaluation(queries_file, mock_search, k=10)

    assert results["num_queries"] == 1
    assert results["mean_precision@10"] == 0.0
    assert results["mean_recall@10"] == 0.0
    assert results["mean_mrr"] == 0.0
    assert results["mean_ndcg@10"] == 0.0


def test_queries_dataset_ground_truth_matches_actual_media_content():
    queries_file = Path(__file__).with_name("queries.json")
    queries = load_queries(queries_file)

    cat_query = next((q for q in queries if q["query_id"] == "q001"), None)
    assert cat_query is not None, "q001 (cat query) must exist"
    assert cat_query["query_text"] == "cat"
    assert 4 not in cat_query["relevant_media_ids"], (
        "media:4 (cat.jpg) actually contains dogs, not a cat. "
        "The evaluation dataset ground truth must match the actual visual content."
    )

    mountain_query = next((q for q in queries if q["query_id"] == "q008"), None)
    assert mountain_query is not None, "q008 (mountain landscape query) must exist"
    assert mountain_query["query_text"] == "mountain landscape"
    assert 8 not in mountain_query["relevant_media_ids"], (
        "media:8 (mountain.jpg) actually depicts a person working with a laptop and smartphone indoors, "
        "not a mountain landscape."
    )

    blue_sky_query = next((q for q in queries if q["query_id"] == "q011"), None)
    assert blue_sky_query is not None, "q011 (blue sky query) must exist"
    assert blue_sky_query["query_text"] == "blue sky"
    assert 8 not in blue_sky_query["relevant_media_ids"], (
        "media:8 (mountain.jpg) is an indoor workspace scene, not blue sky content."
    )

    tree_query = next((q for q in queries if q["query_id"] == "q013"), None)
    assert tree_query is not None, "q013 (tree query) must exist"
    assert tree_query["query_text"] == "tree"
    assert 8 not in tree_query["relevant_media_ids"], (
        "media:8 (mountain.jpg) is an indoor workspace scene, not tree content."
    )
