from __future__ import annotations

from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import MediaItem, ProcessingStatus
from .storage import media_url


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = np.linalg.norm(left)
    right_norm = np.linalg.norm(right)
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _normalize_scores(results: list[dict]) -> list[dict]:
    if not results:
        return results
    scores = [result["score"] for result in results]
    max_score = max(scores)
    min_score = min(scores)
    if max_score == min_score:
        for result in results:
            result["score"] = 1.0
        return results
    for result in results:
        result["score"] = (result["score"] - min_score) / (max_score - min_score)
    return results


def _completed_media(session: Session) -> list[MediaItem]:
    return list(
        session.execute(
            select(MediaItem)
            .options(selectinload(MediaItem.scenes))
            .where(MediaItem.status == ProcessingStatus.COMPLETED)
        ).scalars()
    )


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
                    "media_type": media.media_type,
                    "result_type": "image",
                    "original_filename": media.original_filename,
                    "caption": media.caption or "",
                    "file_url": media_url(settings, media.file_path),
                    "thumbnail_url": media_url(settings, media.file_path),
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
                        "media_type": media.media_type,
                        "result_type": "video_scene",
                        "original_filename": media.original_filename,
                        "caption": scene.caption or "",
                        "file_url": media_url(settings, media.file_path),
                        "thumbnail_url": media_url(settings, scene.thumbnail_path),
                        "start_time": scene.start_time,
                        "end_time": scene.end_time,
                        "score": score,
                    }
                )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: max(top_k * 2, top_k)]


def _keyword_results(settings, session: Session, query_text: str, top_k: int) -> list[dict]:
    corpus: list[str] = []
    payloads: list[dict] = []

    for media in _completed_media(session):
        if media.media_type == "image" and media.caption:
            corpus.append(media.caption)
            payloads.append(
                {
                    "key": ("image", media.id),
                    "media_id": media.id,
                    "media_type": media.media_type,
                    "result_type": "image",
                    "original_filename": media.original_filename,
                    "caption": media.caption or "",
                    "file_url": media_url(settings, media.file_path),
                    "thumbnail_url": media_url(settings, media.file_path),
                    "start_time": None,
                    "end_time": None,
                }
            )

        for scene in media.scenes:
            if scene.caption:
                corpus.append(scene.caption)
                payloads.append(
                    {
                        "key": ("scene", scene.id),
                        "media_id": media.id,
                        "media_type": media.media_type,
                        "result_type": "video_scene",
                        "original_filename": media.original_filename,
                        "caption": scene.caption or "",
                        "file_url": media_url(settings, media.file_path),
                        "thumbnail_url": media_url(settings, scene.thumbnail_path),
                        "start_time": scene.start_time,
                        "end_time": scene.end_time,
                    }
                )

    if not corpus:
        return []

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    query_vec = vectorizer.transform([query_text])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

    results: list[dict] = []
    for index, similarity in enumerate(similarities):
        if similarity <= 0:
            continue
        results.append({**payloads[index], "score": float(similarity)})

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: max(top_k * 2, top_k)]


def search_text(settings, session: Session, query_text: str, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    limit = top_k or settings.search_max_results
    vector_results = _normalize_scores(_vector_results(settings, session, query_embedding, limit))
    keyword_results = _normalize_scores(_keyword_results(settings, session, query_text, limit))

    merged: dict[tuple, dict] = defaultdict(dict)
    for result in vector_results:
        merged[result["key"]].update(result)
        merged[result["key"]]["vector_score"] = result["score"]
        merged[result["key"]].setdefault("keyword_score", 0.0)
    for result in keyword_results:
        merged[result["key"]].update(result)
        merged[result["key"]]["keyword_score"] = result["score"]
        merged[result["key"]].setdefault("vector_score", 0.0)

    output: list[dict] = []
    for item in merged.values():
        score = (
            item.get("vector_score", 0.0) * settings.search_vector_weight
            + item.get("keyword_score", 0.0) * settings.search_keyword_weight
        )
        output.append(
            {
                "media_id": item["media_id"],
                "media_type": item["media_type"],
                "result_type": item["result_type"],
                "original_filename": item["original_filename"],
                "score": round(score * 100, 2),
                "caption": item.get("caption", ""),
                "file_url": item.get("file_url", ""),
                "thumbnail_url": item.get("thumbnail_url", ""),
                "start_time": item.get("start_time"),
                "end_time": item.get("end_time"),
            }
        )

    output.sort(key=lambda item: item["score"], reverse=True)
    return output[:limit]


def search_image(settings, session: Session, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    limit = top_k or settings.search_max_results
    vector_results = _normalize_scores(_vector_results(settings, session, query_embedding, limit))

    output: list[dict] = []
    for item in vector_results:
        output.append(
            {
                "media_id": item["media_id"],
                "media_type": item["media_type"],
                "result_type": item["result_type"],
                "original_filename": item["original_filename"],
                "score": round(item["score"] * 100, 2),
                "caption": item.get("caption", ""),
                "file_url": item.get("file_url", ""),
                "thumbnail_url": item.get("thumbnail_url", ""),
                "start_time": item.get("start_time"),
                "end_time": item.get("end_time"),
            }
        )

    output.sort(key=lambda item: item["score"], reverse=True)
    return output[:limit]
