from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable


def load_queries(file_path: Path) -> list[dict]:
    return json.loads(file_path.read_text())


def compute_metrics(relevant_ids: set[int], retrieved_ids: list[int], k: int = 10) -> dict[str, float]:
    top_k = retrieved_ids[:k]
    hits = sum(1 for item_id in top_k if item_id in relevant_ids)

    precision = hits / k if k else 0.0
    recall = hits / len(relevant_ids) if relevant_ids else 0.0

    mrr = 0.0
    for index, item_id in enumerate(retrieved_ids, start=1):
        if item_id in relevant_ids:
            mrr = 1.0 / index
            break

    dcg = 0.0
    for index, item_id in enumerate(top_k, start=1):
        if item_id in relevant_ids:
            dcg += 1.0 / math.log2(index + 1)

    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    ndcg = dcg / idcg if idcg else 0.0

    return {
        f"precision@{k}": precision,
        f"recall@{k}": recall,
        "mrr": mrr,
        f"ndcg@{k}": ndcg,
    }


def run_evaluation(
    queries_file: Path,
    search_fn: Callable[[str, int], list[dict]],
    k: int = 10,
) -> dict[str, float]:
    queries = load_queries(queries_file)
    all_metrics: list[dict[str, float]] = []

    for query in queries:
        relevant_media_ids = set(query.get("relevant_media_ids", []))
        relevant_scene_ids = set(query.get("relevant_scene_ids", []))
        relevant_ids = relevant_media_ids | relevant_scene_ids

        results = search_fn(query["query_text"], k)
        retrieved_ids = [result["media_id"] for result in results]
        all_metrics.append(compute_metrics(relevant_ids, retrieved_ids, k=k))

    if not all_metrics:
        return {
            f"mean_precision@{k}": 0.0,
            f"mean_recall@{k}": 0.0,
            "mean_mrr": 0.0,
            f"mean_ndcg@{k}": 0.0,
            "num_queries": 0,
        }

    return {
        f"mean_precision@{k}": sum(metric[f"precision@{k}"] for metric in all_metrics) / len(all_metrics),
        f"mean_recall@{k}": sum(metric[f"recall@{k}"] for metric in all_metrics) / len(all_metrics),
        "mean_mrr": sum(metric["mrr"] for metric in all_metrics) / len(all_metrics),
        f"mean_ndcg@{k}": sum(metric[f"ndcg@{k}"] for metric in all_metrics) / len(all_metrics),
        "num_queries": len(all_metrics),
    }
