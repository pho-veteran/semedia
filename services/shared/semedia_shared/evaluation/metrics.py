"""Core evaluation metric computation."""
from __future__ import annotations

import math


VIDEO_EXTENSIONS = (".webm", ".mp4", ".ogv")


def normalize_relevant_id(value, *, kind: str) -> str:
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
            return value
        if value.isdigit():
            return f"scene:{value}"
        return f"scene:{value}"
    raise TypeError(f"Unsupported scene identifier: {value!r}")


def _video_credit_key(identifier: object) -> object:
    if isinstance(identifier, str) and identifier.startswith("scene:"):
        parts = identifier.split(":")
        if len(parts) == 3:
            return f"scene:{parts[1]}"
    return identifier


def _dedupe_preserving_order(values: list[object]) -> list[object]:
    seen: set[object] = set()
    deduped: list[object] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            deduped.append(v)
    return deduped


def compute_metrics(relevant_ids: set[object], retrieved_ids: list[object], k: int = 10) -> dict[str, float]:
    relevant_ids = {_video_credit_key(i) for i in relevant_ids}
    retrieved_ids = _dedupe_preserving_order([_video_credit_key(i) for i in retrieved_ids])
    top_k = retrieved_ids[:k]
    hits = sum(1 for i in top_k if i in relevant_ids)

    precision = hits / k if k else 0.0
    recall = hits / len(relevant_ids) if relevant_ids else 0.0

    mrr = 0.0
    for idx, i in enumerate(top_k, 1):
        if i in relevant_ids:
            mrr = 1.0 / idx
            break

    dcg = sum(1.0 / math.log2(idx + 1) for idx, i in enumerate(top_k, 1) if i in relevant_ids)
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(idx + 1) for idx in range(1, ideal_hits + 1))
    ndcg = dcg / idcg if idcg else 0.0

    return {"precision@k": precision, "recall@k": recall, "mrr": mrr, "ndcg@k": ndcg}


def result_identifier(result: dict) -> str:
    scene_key = result.get("scene_key")
    if scene_key:
        return scene_key
    if result.get("scene_id") is not None:
        return f"scene:{result['scene_id']}"
    return f"media:{result['media_id']}"


def summarize_group(per_query_results: list[dict], key: str, k: int = 10) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = {}
    for r in per_query_results:
        grouped.setdefault(r.get(key, "unknown") or "unknown", []).append(r)
    return {
        gk: {
            f"mean_precision@{k}": sum(r["precision@k"] for r in rows) / len(rows),
            f"mean_recall@{k}": sum(r["recall@k"] for r in rows) / len(rows),
            "mean_mrr": sum(r["mrr"] for r in rows) / len(rows),
            f"mean_ndcg@{k}": sum(r["ndcg@k"] for r in rows) / len(rows),
            "num_queries": len(rows),
        }
        for gk, rows in grouped.items()
    }


def summarize_negative_queries(per_query_results: list[dict], k: int = 10, score_threshold: float = 0.0) -> dict:
    negatives = [r for r in per_query_results if "negative" in r.get("tags", [])]
    if not negatives:
        return {"num_queries": 0, "false_positive_rate": 0.0, "mean_false_positives_per_query": 0.0}
    fp_counts = [sum(1 for s in r.get("retrieved_scores", []) if s >= score_threshold) for r in negatives]
    return {
        "num_queries": len(negatives),
        "false_positive_rate": sum(1 for c in fp_counts if c > 0) / len(negatives),
        "mean_false_positives_per_query": sum(fp_counts) / len(negatives),
    }


def compare_reports(current: dict, baseline: dict, *, k: int = 10, relative_drop_threshold: float = 0.05) -> dict:
    metric_names = [f"mean_precision@{k}", f"mean_recall@{k}", "mean_mrr", f"mean_ndcg@{k}"]
    deltas = {}
    regressions = []
    for name in metric_names:
        bv = baseline.get(name, 0.0)
        cv = current.get(name, 0.0)
        deltas[name] = cv - bv
        if bv > 0 and cv < bv * (1 - relative_drop_threshold):
            regressions.append(name)

    bn = baseline.get("negative_queries", {}).get("false_positive_rate", 0.0)
    cn = current.get("negative_queries", {}).get("false_positive_rate", 0.0)
    deltas["negative_false_positive_rate"] = cn - bn
    if cn > bn + 0.05:
        regressions.append("negative_false_positive_rate")

    return {"status": "regression" if regressions else "ok", "regressions": regressions, "deltas": deltas}
