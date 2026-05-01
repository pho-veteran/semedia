#!/usr/bin/env python3
"""
Run offline evaluation against a live Semedia instance.

Usage:
    python testing/evaluation/run_evaluation.py --base-url http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

from evaluate_search import load_queries, run_evaluation


def search_text_via_api(base_url: str, query_text: str, top_k: int) -> list[dict]:
    """Execute text search against Semedia API and return results."""
    body = json.dumps({"query_text": query_text, "top_k": top_k}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/api/v1/search/",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload["results"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline evaluation against live Semedia instance.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL of gateway API")
    parser.add_argument("--queries", default=None, help="Path to queries.json (default: testing/evaluation/queries.json)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to retrieve per query")
    args = parser.parse_args()

    if args.queries:
        queries_file = Path(args.queries)
    else:
        queries_file = Path(__file__).parent / "queries.json"

    if not queries_file.exists():
        print(f"Error: queries file not found: {queries_file}", file=sys.stderr)
        return 1

    print(f"Loading queries from {queries_file}")
    queries = load_queries(queries_file)
    judged_queries = [q for q in queries if q.get("relevant_media_ids") or q.get("relevant_scene_ids")]

    print(f"Total queries: {len(queries)}")
    print(f"Judged queries: {len(judged_queries)}")

    if not judged_queries:
        print("Error: No judged queries found. Populate relevant_media_ids and relevant_scene_ids first.", file=sys.stderr)
        return 1

    print(f"\nRunning evaluation against {args.base_url}")
    print("=" * 80)

    def search_fn(query_text: str, top_k: int) -> list[dict]:
        return search_text_via_api(args.base_url, query_text, top_k)

    try:
        results = run_evaluation(queries_file, search_fn, k=args.top_k)
    except Exception as exc:
        print(f"Error during evaluation: {exc}", file=sys.stderr)
        return 1

    print("\nEvaluation Results:")
    print("=" * 80)
    print(f"Queries evaluated: {results['num_queries']}")
    print(f"Precision@{args.top_k}: {results[f'mean_precision@{args.top_k}']:.4f}")
    print(f"Recall@{args.top_k}: {results[f'mean_recall@{args.top_k}']:.4f}")
    print(f"MRR: {results['mean_mrr']:.4f}")
    print(f"NDCG@{args.top_k}: {results[f'mean_ndcg@{args.top_k}']:.4f}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
