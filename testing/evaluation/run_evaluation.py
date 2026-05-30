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

try:
    from .benchmark_validation import validate_benchmark_artifacts
    from .evaluate_search import compare_reports, load_queries, run_evaluation
except ImportError:
    from benchmark_validation import validate_benchmark_artifacts
    from evaluate_search import compare_reports, load_queries, run_evaluation



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


def search_image_via_api(base_url: str, image_path: str, top_k: int) -> list[dict]:
    """Execute by-image search against Semedia API and return results."""
    from uuid import uuid4
    import mimetypes

    file_path = Path(image_path)
    boundary = f"----SemediaBoundary{uuid4().hex}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()

    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="top_k"\r\n\r\n'
            f"{top_k}\r\n"
        ).encode("utf-8"),
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)

    request = urllib.request.Request(
        f"{base_url}/api/v1/search/by-image/",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
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
    parser.add_argument("--per-query", action="store_true", help="Print per-query metrics and retrieved IDs")
    parser.add_argument("--by-type", action="store_true", help="Print aggregate metrics grouped by query type")
    parser.add_argument("--output", default=None, help="Write the evaluation report JSON to this path")
    parser.add_argument("--compare-to", default=None, help="Path to a saved baseline report JSON")
    parser.add_argument(
        "--relative-drop-threshold",
        type=float,
        default=0.05,
        help="Relative metric drop that should be flagged as a regression",
    )
    parser.add_argument(
        "--by-image-queries",
        default=None,
        help="Path to a JSON file mapping image filenames (under assets/) to expected relevant IDs for by-image evaluation",
    )
    args = parser.parse_args()


    def print_metric_block(title: str, metrics: dict) -> None:
        print(f"\n{title}")
        print("=" * 80)
        print(f"Queries evaluated: {metrics['num_queries']}")
        print(f"Precision@{args.top_k}: {metrics[f'mean_precision@{args.top_k}']:.4f}")
        print(f"Recall@{args.top_k}: {metrics[f'mean_recall@{args.top_k}']:.4f}")
        print(f"MRR: {metrics['mean_mrr']:.4f}")
        print(f"NDCG@{args.top_k}: {metrics[f'mean_ndcg@{args.top_k}']:.4f}")
        print("=" * 80)

    def print_per_query(results: list[dict]) -> None:
        print("\nPer-query Results:")
        print("=" * 80)
        for result in results:
            print(f"[{result['query_id']}] {result['query_text']} ({result['query_type']})")
            print(
                f"  P@{args.top_k}={result['precision@k']:.4f} "
                f"R@{args.top_k}={result['recall@k']:.4f} "
                f"MRR={result['mrr']:.4f} "
                f"NDCG@{args.top_k}={result['ndcg@k']:.4f}"
            )
            print(f"  Retrieved: {', '.join(result['retrieved_ids']) if result['retrieved_ids'] else 'none'}")

    def print_by_type(by_type: dict[str, dict]) -> None:
        print("\nMetrics by Query Type:")
        print("=" * 80)
        for query_type, metrics in sorted(by_type.items()):
            print_metric_block(f"{query_type.title()} queries", metrics)

    if args.queries:
        queries_file = Path(args.queries)
    else:
        queries_file = Path(__file__).parent / "queries.json"

    if not queries_file.exists():
        print(f"Error: queries file not found: {queries_file}", file=sys.stderr)
        return 1

    audit_log_file = Path(__file__).parent / "audit_log.json"

    print(f"Loading queries from {queries_file}")
    validate_benchmark_artifacts(queries_file, audit_log_file)
    queries = load_queries(queries_file)
    judged_queries = [
        q
        for q in queries
        if q.get("judged") or q.get("relevant_media_ids") or q.get("relevant_scene_ids")
    ]

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
    except Exception as exc:
        print(f"Error during evaluation: {exc}", file=sys.stderr)
        return 1

    print_metric_block("Evaluation Results:", results)

    if args.per_query:
        print_per_query(results.get("per_query", []))

    if args.by_type:
        print_by_type(results.get("by_type", {}))

    if "negative_queries" in results:
        negatives = results["negative_queries"]
        print("\nNegative-query Summary")
        print("=" * 80)
        print(f"Queries evaluated: {negatives['num_queries']}")
        print(f"False positive rate: {negatives['false_positive_rate']:.4f}")
        print(f"Mean false positives/query: {negatives['mean_false_positives_per_query']:.4f}")

    payload = {"report": results}

    if args.by_image_queries:
        by_image_file = Path(args.by_image_queries)
        if not by_image_file.exists():
            print(f"Error: by-image queries file not found: {by_image_file}", file=sys.stderr)
            return 1
        by_image_spec = json.loads(by_image_file.read_text())
        assets_dir = by_image_file.parent / "assets"
        print(f"\nRunning by-image evaluation ({len(by_image_spec)} queries)")
        for entry in by_image_spec:
            image_file = assets_dir / entry["filename"]
            results_list = search_image_via_api(args.base_url, str(image_file), args.top_k)
            print(f"  [{entry['filename']}] returned {len(results_list)} results")
        payload["by_image"] = {"num_queries": len(by_image_spec)}

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
        print(f"\nComparison status: {comparison['status']}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2))
        print(f"\nSaved evaluation report to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
