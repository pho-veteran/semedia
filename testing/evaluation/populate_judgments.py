#!/usr/bin/env python3
"""
Populate relevance judgments for Phase 1 baseline evaluation.

This script runs each query against the current Semedia system,
displays results, and allows manual judgment of relevance.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path


def search_text(base_url: str, query_text: str, top_k: int = 10) -> list[dict]:
    """Execute text search against Semedia API."""
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


def main():
    base_url = "http://127.0.0.1:8000"
    queries_file = Path(__file__).parent / "queries.json"
    queries = json.loads(queries_file.read_text())

    print(f"Running {len(queries)} queries against {base_url}")
    print("=" * 80)

    for query in queries:
        query_id = query["query_id"]
        query_text = query["query_text"]
        query_type = query["query_type"]

        print(f"\n[{query_id}] {query_text} ({query_type})")
        print("-" * 80)

        results = search_text(base_url, query_text, top_k=10)

        if not results:
            print("  No results returned")
            continue

        for idx, result in enumerate(results, start=1):
            media_id = result["media_id"]
            scene_id = result.get("scene_id")
            score = result["score"]
            caption = result["caption"]
            result_type = result["result_type"]

            if result_type == "scene":
                print(f"  {idx}. [scene:{scene_id}] media:{media_id} | score={score:.2f}")
            else:
                print(f"  {idx}. [media:{media_id}] | score={score:.2f}")
            print(f"      {caption}")

    print("\n" + "=" * 80)
    print("Review the results above and manually populate relevant_media_ids")
    print("and relevant_scene_ids in testing/evaluation/queries.json")


if __name__ == "__main__":
    main()
