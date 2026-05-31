from __future__ import annotations

import json
import sys
from pathlib import Path

from testing.evaluation import run_evaluation as run_evaluation_cli
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
        "mean_precision@10": 0.05,
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
    assert saved["report"]["num_queries"] == 1
    assert saved["report"]["negative_queries"]["num_queries"] == 1
    assert saved["comparison"]["status"] == "ok"


def test_cli_runner_saves_output_and_compares_baseline(tmp_path, monkeypatch, capsys):
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
                        "query_text": "test query",
                        "query_type": "object",
                        "media_type_target": "image",
                        "difficulty": "easy",
                        "tags": ["positive"],
                        "judged": True,
                        "relevant_media_ids": [1],
                        "relevant_scene_ids": [],
                        "notes": "Manual review confirmed.",
                    }
                ],
            }
        )
    )
    # Strict CLI validation requires a co-located locked manifest + assets.
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "sample.jpg").write_bytes(b"x")
    (tmp_path / "asset_manifest.json").write_text(
        json.dumps([{"asset_id": "a1", "filename": "sample.jpg"}])
    )

    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(
        json.dumps(
            {
                "report": {
                    "mean_precision@10": 0.05,
                    "mean_recall@10": 0.5,
                    "mean_mrr": 0.5,
                    "mean_ndcg@10": 0.5,
                    "negative_queries": {"false_positive_rate": 0.0},
                }
            }
        )
    )

    output_file = tmp_path / "output.json"

    monkeypatch.setattr(
        run_evaluation_cli,
        "search_text_via_api",
        lambda base_url, query_text, top_k: [{"media_id": 1, "scene_id": None, "score": 0.9}],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_evaluation.py",
            "--queries",
            str(queries_file),
            "--output",
            str(output_file),
            "--compare-to",
            str(baseline_file),
        ],
    )

    exit_code = run_evaluation_cli.main()

    assert exit_code == 0, "CLI runner returned non-zero exit code"
    assert output_file.exists(), "Output file was not created"

    saved = json.loads(output_file.read_text())
    assert "report" in saved
    assert "comparison" in saved
    assert saved["report"]["num_queries"] == 1
    assert saved["comparison"]["status"] in {"ok", "regression"}

    captured = capsys.readouterr()
    assert "Comparison status:" in captured.out
    assert "Saved evaluation report to" in captured.out



def test_by_image_search_via_api_feeds_evaluation(tmp_path, monkeypatch, capsys):
    """E4: search_image_via_api is reusable and can feed run_evaluation via CLI."""
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
                        "query_text": "test query",
                        "query_type": "object",
                        "media_type_target": "image",
                        "difficulty": "easy",
                        "tags": ["positive"],
                        "judged": True,
                        "relevant_media_ids": [1],
                        "relevant_scene_ids": [],
                        "notes": "Manual review confirmed.",
                    }
                ],
            }
        )
    )
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "sample.jpg").write_bytes(b"\xff\xd8\xff\xe0fake")
    (tmp_path / "asset_manifest.json").write_text(
        json.dumps([{"asset_id": "a1", "filename": "sample.jpg"}])
    )

    by_image_file = tmp_path / "by_image_queries.json"
    by_image_file.write_text(
        json.dumps([{"filename": "sample.jpg", "relevant_media_ids": [1]}])
    )

    output_file = tmp_path / "output.json"

    monkeypatch.setattr(
        run_evaluation_cli,
        "search_text_via_api",
        lambda base_url, query_text, top_k: [{"media_id": 1, "scene_id": None, "score": 0.9}],
    )
    monkeypatch.setattr(
        run_evaluation_cli,
        "search_image_via_api",
        lambda base_url, image_path, top_k: [{"media_id": 1, "scene_id": None, "score": 0.85}],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_evaluation.py",
            "--queries",
            str(queries_file),
            "--output",
            str(output_file),
            "--by-image-queries",
            str(by_image_file),
        ],
    )

    exit_code = run_evaluation_cli.main()

    assert exit_code == 0, "CLI runner returned non-zero exit code"
    assert output_file.exists(), "Output file was not created"

    saved = json.loads(output_file.read_text())
    assert "report" in saved
    assert saved["report"]["num_queries"] == 1
    assert "by_image" in saved
    assert saved["by_image"]["num_queries"] == 1

    # Verify search_image_via_api is independently callable and returns results.
    results = run_evaluation_cli.search_image_via_api("http://fake", str(tmp_path / "assets" / "sample.jpg"), 10)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["media_id"] == 1
