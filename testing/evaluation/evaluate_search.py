from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable

try:
    from .benchmark_validation import load_benchmark_definition, normalize_relevant_id
except ImportError:
    from benchmark_validation import load_benchmark_definition, normalize_relevant_id



def load_queries(file_path: Path) -> list[dict]:
    return load_benchmark_definition(file_path)["queries"]


def _dedupe_preserving_order(values: list[object]) -> list[object]:
    deduped: list[object] = []
    seen: set[object] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _video_credit_key(identifier: object) -> object:
    # Credit any scene of the correct parent video: scene:<file>:<index> -> scene:<file>.
    # Runtime scene indices shift across re-seeding, so judge video hits at video granularity.
    if isinstance(identifier, str) and identifier.startswith("scene:"):
        parts = identifier.split(":")
        if len(parts) == 3:
            return f"scene:{parts[1]}"
    return identifier


def compute_metrics(relevant_ids: set[object], retrieved_ids: list[object], k: int = 10) -> dict[str, float]:
    relevant_ids = {_video_credit_key(item_id) for item_id in relevant_ids}
    retrieved_ids = _dedupe_preserving_order([_video_credit_key(item_id) for item_id in retrieved_ids])
    top_k = retrieved_ids[:k]
    hits = sum(1 for item_id in top_k if item_id in relevant_ids)

    precision = hits / k if k else 0.0
    recall = hits / len(relevant_ids) if relevant_ids else 0.0

    mrr = 0.0
    for index, item_id in enumerate(top_k, start=1):
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


def summarize_negative_queries(per_query_results: list[dict], k: int, score_threshold: float = 0.0) -> dict[str, float]:
    negatives = [row for row in per_query_results if "negative" in row.get("tags", [])]
    if not negatives:
        return {"num_queries": 0, "false_positive_rate": 0.0, "mean_false_positives_per_query": 0.0, "score_threshold": score_threshold}

    false_positive_counts = [
        sum(1 for score in row.get("retrieved_scores", []) if score >= score_threshold)
        for row in negatives
    ]
    queries_with_false_positives = sum(1 for count in false_positive_counts if count > 0)

    return {
        "num_queries": len(negatives),
        "false_positive_rate": queries_with_false_positives / len(negatives),
        "mean_false_positives_per_query": sum(false_positive_counts) / len(negatives),
        "score_threshold": score_threshold,
    }


def compare_reports(
    current_report: dict,
    baseline_report: dict,
    *,
    k: int,
    relative_drop_threshold: float = 0.05,
) -> dict:
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


def _result_identifier(result: dict) -> str:
    scene_key = result.get("scene_key")
    if scene_key:
        return scene_key
    if result.get("scene_id") is not None:
        return f"scene:{result['scene_id']}"
    return f"media:{result['media_id']}"


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
    negative_score_threshold: float = 0.0,
) -> dict:
    queries = load_queries(queries_file)
    judged_queries = [
        query
        for query in queries
        if query.get("judged")
        or query.get("relevant_media_ids")
        or query.get("relevant_scene_ids")
    ]
    all_metrics: list[dict[str, float]] = []
    per_query_results: list[dict] = []
    collect_per_query = any(
        [
            include_per_query,
            include_by_type,
            include_by_modality,
            include_by_difficulty,
            include_negative_summary,
        ]
    )

    for query in judged_queries:
        relevant_media_ids = set(query.get("relevant_media_ids", []))
        relevant_scene_ids = set(query.get("relevant_scene_ids", []))
        relevant_ids = {
            *(normalize_relevant_id(item_id, kind="media") for item_id in relevant_media_ids),
            *(normalize_relevant_id(item_id, kind="scene") for item_id in relevant_scene_ids),
        }

        results = search_fn(query["query_text"], k)
        retrieved_ids = []
        retrieved_scores = []
        seen_ids: set[object] = set()
        for result in results:
            identifier = _result_identifier(result)
            if identifier in seen_ids:
                continue
            seen_ids.add(identifier)
            retrieved_ids.append(identifier)
            retrieved_scores.append(round(float(result.get("score", 0.0)), 4))
        metrics = compute_metrics(relevant_ids, retrieved_ids, k=k)
        if "negative" not in query.get("tags", []):
            all_metrics.append(metrics)

        if collect_per_query:
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
                    "retrieved_scores": retrieved_scores[:k],
                }
            )

    result = {
        f"mean_precision@{k}": 0.0,
        f"mean_recall@{k}": 0.0,
        "mean_mrr": 0.0,
        f"mean_ndcg@{k}": 0.0,
        "num_queries": len(all_metrics),
        "num_negative_queries": sum(1 for query in judged_queries if "negative" in query.get("tags", [])),
    }

    if all_metrics:
        result.update(
            {
                f"mean_precision@{k}": sum(metric[f"precision@{k}"] for metric in all_metrics) / len(all_metrics),
                f"mean_recall@{k}": sum(metric[f"recall@{k}"] for metric in all_metrics) / len(all_metrics),
                "mean_mrr": sum(metric["mrr"] for metric in all_metrics) / len(all_metrics),
                f"mean_ndcg@{k}": sum(metric[f"ndcg@{k}"] for metric in all_metrics) / len(all_metrics),
            }
        )

    if include_per_query:
        result["per_query"] = per_query_results

    # Negatives are scored only via summarize_negative_queries; keep them out of positive slices.
    positive_results = [row for row in per_query_results if "negative" not in row.get("tags", [])]
    if include_by_type:
        result["by_type"] = summarize_group(positive_results, "query_type", k)
    if include_by_modality:
        result["by_modality"] = summarize_group(positive_results, "media_type_target", k)
    if include_by_difficulty:
        result["by_difficulty"] = summarize_group(positive_results, "difficulty", k)
    if include_negative_summary:
        result["negative_queries"] = summarize_negative_queries(per_query_results, k, negative_score_threshold)

    return result
