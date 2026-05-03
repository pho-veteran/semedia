from __future__ import annotations

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .index_service import ensure_keyword_index_current, search_keyword
from .models import MediaItem, ProcessingStatus
from .ranking_service import build_result_explanation, merge_candidates, rank_candidates
from .storage import media_url


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = np.linalg.norm(left)
    right_norm = np.linalg.norm(right)
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _normalize_scores(results: list[dict]) -> list[dict]:
    for result in results:
        result["score"] = max(0.0, min(1.0, float(result["score"])))
    return results


def _completed_media(session: Session) -> list[MediaItem]:
    return list(
        session.execute(
            select(MediaItem)
            .options(selectinload(MediaItem.scenes))
            .where(MediaItem.status == ProcessingStatus.COMPLETED)
        ).scalars()
    )


def _serialize_score(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _stable_scene_key(item: dict) -> str | None:
    scene_index = item.get("scene_index")
    if scene_index is None or not item.get("original_filename"):
        return None
    return f"scene:{item['original_filename']}:{scene_index}"


def _serialize_ranked_result(item: dict, *, query_text: str | None, query_mode: str) -> dict:
    return {
        "media_id": item["media_id"],
        "scene_id": item.get("scene_id"),
        "scene_index": item.get("scene_index"),
        "scene_key": _stable_scene_key(item),
        "media_type": item["media_type"],
        "result_type": item["result_type"],
        "original_filename": item["original_filename"],
        "score": _serialize_score(item["score"]),
        "vector_score": _serialize_score(item.get("vector_score", 0.0)),
        "keyword_score": _serialize_score(item.get("keyword_score", 0.0)),
        "caption": item.get("caption", ""),
        "file_url": item.get("file_url", ""),
        "thumbnail_url": item.get("thumbnail_url", ""),
        "file_size": item.get("file_size", 0),
        "created_at": item.get("created_at"),
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "explanation": build_result_explanation(item, query_text=query_text, query_mode=query_mode),
    }


def _vector_results(settings, session: Session, query_embedding: list[float], top_k: int) -> list[dict]:
    query = np.array(query_embedding, dtype=np.float32)
    results: list[dict] = []

    for media in _completed_media(session):
        if media.media_type == "image" and media.embedding:
            score = _cosine(query, np.array(media.embedding, dtype=np.float32))
            results.append(
                {
                    "key": ("image", media.id),
                    "media_id": media.id,
                    "scene_id": None,
                    "scene_index": None,
                    "media_type": media.media_type,
                    "result_type": "image",
                    "original_filename": media.original_filename,
                    "caption": media.caption or "",
                    "file_url": media_url(settings, media.file_path),
                    "thumbnail_url": media_url(settings, media.file_path),
                    "file_size": media.file_size,
                    "created_at": media.uploaded_at,
                    "start_time": None,
                    "end_time": None,
                    "score": score,
                }
            )

        for scene in media.scenes:
            if scene.embedding:
                score = _cosine(query, np.array(scene.embedding, dtype=np.float32))
                results.append(
                    {
                        "key": ("scene", scene.id),
                        "media_id": media.id,
                        "scene_id": scene.id,
                        "scene_index": scene.scene_index,
                        "media_type": media.media_type,
                        "result_type": "video_scene",
                        "original_filename": media.original_filename,
                        "caption": scene.caption or "",
                        "file_url": media_url(settings, media.file_path),
                        "thumbnail_url": media_url(settings, scene.thumbnail_path),
                        "file_size": media.file_size,
                        "created_at": media.uploaded_at,
                        "start_time": scene.start_time,
                        "end_time": scene.end_time,
                        "score": score,
                    }
                )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: max(top_k * 2, top_k)]


def _keyword_results(settings, session: Session, query_text: str, top_k: int) -> list[dict]:
    index_data = ensure_keyword_index_current(settings, session)
    if index_data is None:
        return []
    return search_keyword(query_text, index_data, top_k)


def search_text(settings, session: Session, query_text: str, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    limit = top_k or settings.search_max_results
    vector_results = _normalize_scores(_vector_results(settings, session, query_embedding, limit))
    keyword_results = _normalize_scores(_keyword_results(settings, session, query_text, limit))
    candidates = merge_candidates(vector_results, keyword_results)
    ranked = rank_candidates(settings, candidates, query_text=query_text, query_mode="text", limit=limit)

    return [
        _serialize_ranked_result(item, query_text=query_text, query_mode="text")
        for item in ranked[:limit]
    ]


def search_image(settings, session: Session, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    limit = top_k or settings.search_max_results
    vector_results = _normalize_scores(_vector_results(settings, session, query_embedding, limit))
    candidates = merge_candidates(vector_results, [])
    ranked = rank_candidates(settings, candidates, query_text=None, query_mode="image", limit=limit)

    return [
        _serialize_ranked_result(item, query_text=None, query_mode="image")
        for item in ranked[:limit]
    ]
