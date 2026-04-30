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
            return [{"media_id": 1, "score": 95.0}, {"media_id": 3, "score": 80.0}]
        else:
            return [{"media_id": 4, "score": 90.0}, {"media_id": 2, "score": 85.0}]

    results = run_evaluation(queries_file, mock_search, k=10)

    assert "mean_precision@10" in results
    assert "mean_recall@10" in results
    assert "mean_mrr" in results
    assert "mean_ndcg@10" in results
    assert results["num_queries"] == 2
