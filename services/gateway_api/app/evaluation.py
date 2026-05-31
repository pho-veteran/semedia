"""Evaluation endpoints: SSE run, baselines, and queries."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Generator

import requests
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from semedia_shared.config import get_settings
from semedia_shared.database import build_engine, build_session_factory
from semedia_shared.models import EvaluationRun, MediaItem
from semedia_shared.storage import media_url
from semedia_shared.evaluation import (
    compare_reports,
    compute_metrics,
    load_queries,
    normalize_relevant_id,
    result_identifier,
    summarize_group,
    summarize_negative_queries,
)

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])
settings = get_settings("gateway-api")
_SessionLocal = build_session_factory(build_engine(settings.database_url))

EVAL_DIR = Path(os.environ.get("EVALUATION_DATA_DIR", "/app/evaluation"))


def _queries_file() -> Path:
    return EVAL_DIR / "queries.json"


def _baselines_dir() -> Path:
    return EVAL_DIR / "baselines"


def _search(query_text: str, top_k: int) -> list[dict]:
    response = requests.post(
        f"{settings.search_api_url}/api/v1/search/",
        json={"query_text": query_text, "top_k": top_k},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["results"]


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _expected_results(session, query: dict) -> list[dict]:
    """Resolve a query's ground-truth ids to renderable thumbnails/captions."""
    items: list[dict] = []
    for mid in query.get("relevant_media_ids", []):
        media = session.get(MediaItem, int(mid))
        if media is None:
            continue
        items.append({
            "key": f"media:{media.id}",
            "result_type": "image" if media.media_type == "image" else "video",
            "original_filename": media.original_filename,
            "thumbnail_url": media_url(settings, media.file_path),
            "caption": media.caption or "",
        })
    for sid in query.get("relevant_scene_ids", []):
        parts = str(sid).split(":")
        if len(parts) != 3:
            continue
        _, filename, scene_index = parts
        media = session.execute(
            select(MediaItem).options(selectinload(MediaItem.scenes)).where(MediaItem.original_filename == filename)
        ).scalar_one_or_none()
        if media is None:
            continue
        scene = next((s for s in media.scenes if str(s.scene_index) == scene_index), None) or (
            media.scenes[0] if media.scenes else None
        )
        items.append({
            "key": f"scene:{filename}",
            "result_type": "video_scene",
            "original_filename": media.original_filename,
            "thumbnail_url": media_url(settings, scene.thumbnail_path) if scene else media_url(settings, media.file_path),
            "caption": (scene.caption if scene else media.caption) or "",
        })
    return items


def _run_generator(top_k: int, compare_to: str | None) -> Generator[str, None, None]:
    qf = _queries_file()
    if not qf.exists():
        yield _sse_event({"type": "error", "message": "queries.json not found"})
        return

    queries = load_queries(qf)
    judged = [q for q in queries if q.get("judged") or q.get("relevant_media_ids") or q.get("relevant_scene_ids")]
    total = len(judged)

    yield _sse_event({"type": "start", "total_queries": total})

    all_metrics: list[dict] = []
    per_query_results: list[dict] = []

    for idx, query in enumerate(judged):
        relevant_ids = {
            *(normalize_relevant_id(mid, kind="media") for mid in query.get("relevant_media_ids", [])),
            *(normalize_relevant_id(sid, kind="scene") for sid in query.get("relevant_scene_ids", [])),
        }

        try:
            results = _search(query["query_text"], top_k)
        except Exception as exc:
            yield _sse_event({"type": "query_error", "query_id": query["query_id"], "error": str(exc)})
            continue

        retrieved_ids = []
        retrieved_scores = []
        seen: set[str] = set()
        for r in results:
            rid = result_identifier(r)
            if rid not in seen:
                seen.add(rid)
                retrieved_ids.append(rid)
                retrieved_scores.append(round(float(r.get("score", 0.0)), 4))

        metrics = compute_metrics(relevant_ids, retrieved_ids, k=top_k)
        is_negative = "negative" in query.get("tags", [])

        if not is_negative:
            all_metrics.append(metrics)

        with _SessionLocal() as _session:
            expected = _expected_results(_session, query)

        per_query_row = {
            "query_id": query["query_id"],
            "query_text": query["query_text"],
            "query_type": query.get("query_type", "unknown"),
            "media_type_target": query.get("media_type_target", "mixed"),
            "difficulty": query.get("difficulty", "unknown"),
            "tags": query.get("tags", []),
            "precision@k": metrics["precision@k"],
            "recall@k": metrics["recall@k"],
            "mrr": metrics["mrr"],
            "ndcg@k": metrics["ndcg@k"],
            "retrieved_ids": retrieved_ids[:top_k],
            "retrieved_scores": retrieved_scores[:top_k],
            "retrieved_results": results[:top_k],
            "relevant_ids": list(relevant_ids),
            "expected_results": expected,
        }
        per_query_results.append(per_query_row)

        # Running aggregates (positive queries only)
        running = {}
        if all_metrics:
            n = len(all_metrics)
            running = {
                "mean_precision@k": sum(m["precision@k"] for m in all_metrics) / n,
                "mean_recall@k": sum(m["recall@k"] for m in all_metrics) / n,
                "mean_mrr": sum(m["mrr"] for m in all_metrics) / n,
                "mean_ndcg@k": sum(m["ndcg@k"] for m in all_metrics) / n,
                "num_positive_queries": n,
            }

        yield _sse_event({
            "type": "query_result",
            "index": idx,
            "total": total,
            **per_query_row,
            "running_aggregate": running,
        })

    # Final summary
    positive_results = [r for r in per_query_results if "negative" not in r.get("tags", [])]
    summary = {
        "type": "summary",
        "num_queries": len(all_metrics),
        "num_negative_queries": total - len(all_metrics),
        "mean_precision@k": sum(m["precision@k"] for m in all_metrics) / len(all_metrics) if all_metrics else 0.0,
        "mean_recall@k": sum(m["recall@k"] for m in all_metrics) / len(all_metrics) if all_metrics else 0.0,
        "mean_mrr": sum(m["mrr"] for m in all_metrics) / len(all_metrics) if all_metrics else 0.0,
        "mean_ndcg@k": sum(m["ndcg@k"] for m in all_metrics) / len(all_metrics) if all_metrics else 0.0,
        "by_type": summarize_group(positive_results, "query_type", top_k),
        "by_modality": summarize_group(positive_results, "media_type_target", top_k),
        "by_difficulty": summarize_group(positive_results, "difficulty", top_k),
        "negative_queries": summarize_negative_queries(per_query_results, top_k),
    }

    if compare_to:
        baseline_path = _baselines_dir() / f"{compare_to}.json"
        if baseline_path.exists():
            baseline_data = json.loads(baseline_path.read_text())
            baseline_report = baseline_data.get("report", baseline_data)
            summary["comparison"] = compare_reports(summary, baseline_report, k=top_k)

    # Persist the run so results survive reloads.
    try:
        session = _SessionLocal()
        run = EvaluationRun(
            top_k=top_k,
            compare_to=compare_to,
            num_queries=len(per_query_results),
            summary={k: v for k, v in summary.items() if k != "type"},
            results=per_query_results,
        )
        session.add(run)
        session.commit()
        summary["run_id"] = run.id
        summary["created_at"] = run.created_at.isoformat()
        session.close()
    except Exception:
        pass

    yield _sse_event(summary)


@router.get("/run")
def run_evaluation(top_k: int = Query(default=10), compare_to: str | None = Query(default=None)):
    return StreamingResponse(
        _run_generator(top_k, compare_to),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/runs")
def list_runs(limit: int = Query(default=20)):
    session = _SessionLocal()
    try:
        rows = session.execute(
            select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit)
        ).scalars().all()
        return {
            "runs": [
                {
                    "id": r.id,
                    "created_at": r.created_at.isoformat(),
                    "top_k": r.top_k,
                    "num_queries": r.num_queries,
                    "mean_precision@k": (r.summary or {}).get("mean_precision@k"),
                    "mean_recall@k": (r.summary or {}).get("mean_recall@k"),
                    "mean_mrr": (r.summary or {}).get("mean_mrr"),
                    "mean_ndcg@k": (r.summary or {}).get("mean_ndcg@k"),
                }
                for r in rows
            ]
        }
    finally:
        session.close()


@router.get("/runs/{run_id}")
def get_run(run_id: int):
    session = _SessionLocal()
    try:
        run = session.get(EvaluationRun, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")
        return {
            "id": run.id,
            "created_at": run.created_at.isoformat(),
            "top_k": run.top_k,
            "compare_to": run.compare_to,
            "summary": run.summary,
            "results": run.results,
        }
    finally:
        session.close()


@router.get("/queries")
def get_queries():
    qf = _queries_file()
    if not qf.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="queries.json not found")
    return json.loads(qf.read_text())


@router.get("/baselines")
def list_baselines():
    bd = _baselines_dir()
    if not bd.exists():
        return {"baselines": []}
    files = sorted(f.stem for f in bd.glob("*.json"))
    return {"baselines": files}


@router.get("/baselines/{name}")
def get_baseline(name: str):
    path = _baselines_dir() / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Baseline '{name}' not found")
    return json.loads(path.read_text())
