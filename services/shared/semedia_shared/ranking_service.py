from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_EXACT_PHRASE_BOOST = 0.08
_RICH_CAPTION_BOOST = 0.02
_RICH_CAPTION_LENGTH = 50
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _caption_key(caption: str) -> str:
    return _normalize_text(caption)


def _tokenize(value: str) -> set[str]:
    return set(_TOKEN_PATTERN.findall(value.lower()))


def merge_candidates(vector_results: list[dict], keyword_results: list[dict]) -> list[dict]:
    merged: dict[tuple, dict] = {}

    for result in vector_results:
        key = result["key"]
        item = merged.setdefault(key, {**result, "vector_score": 0.0, "keyword_score": 0.0})
        item.update({field: value for field, value in result.items() if field != "score"})
        item["vector_score"] = _clamp_score(result["score"])

    for result in keyword_results:
        key = result["key"]
        item = merged.setdefault(key, {**result, "vector_score": 0.0, "keyword_score": 0.0})
        item.update({field: value for field, value in result.items() if field != "score"})
        item["keyword_score"] = _clamp_score(result["score"])

    return list(merged.values())


def _apply_reranking(settings, candidates: list[dict], query_text: str) -> list[dict]:
    normalized_query = _normalize_text(query_text)

    for candidate in candidates:
        rerank_score = candidate.get("rerank_score", candidate.get("fusion_score", 0.0))
        caption = candidate.get("caption", "")
        normalized_caption = _normalize_text(caption)

        if normalized_query and normalized_query in normalized_caption:
            rerank_score += _EXACT_PHRASE_BOOST

        if len(caption.strip()) > _RICH_CAPTION_LENGTH:
            rerank_score += _RICH_CAPTION_BOOST

        candidate["rerank_score"] = _clamp_score(rerank_score)

    return candidates


def _apply_diversity(settings, candidates: list[dict], limit: int, *, dedupe_captions: bool) -> list[dict]:
    diversified: list[dict] = []
    media_counts: dict[int, int] = {}
    seen_captions: set[str] = set()

    for candidate in candidates:
        media_id = candidate["media_id"]
        if media_counts.get(media_id, 0) >= settings.search_max_per_media:
            continue

        if dedupe_captions:
            caption_key = _caption_key(candidate.get("caption", ""))
            if caption_key:
                if caption_key in seen_captions:
                    continue
                seen_captions.add(caption_key)

        media_counts[media_id] = media_counts.get(media_id, 0) + 1
        diversified.append(candidate)
        if len(diversified) >= limit:
            break

    return diversified


def _calibrate_scores(candidates: list[dict]) -> list[dict]:
    for candidate in candidates:
        candidate["score"] = round(_clamp_score(candidate.get("rerank_score", candidate.get("fusion_score", 0.0))), 4)
    return candidates


def build_result_explanation(candidate: dict, *, query_text: str | None, query_mode: str) -> dict:
    vector_score = _clamp_score(candidate.get("vector_score", 0.0))
    keyword_score = _clamp_score(candidate.get("keyword_score", 0.0))
    fusion_score = _clamp_score(candidate.get("fusion_score", vector_score if query_mode == "image" else 0.0))
    rerank_score = _clamp_score(candidate.get("rerank_score", fusion_score))

    normalized_query = _normalize_text(query_text or "")
    normalized_caption = _normalize_text(candidate.get("caption", ""))
    exact_phrase_match = bool(query_mode == "text" and normalized_query and normalized_query in normalized_caption)
    rich_caption = bool(
        query_mode == "text" and len(candidate.get("caption", "").strip()) > _RICH_CAPTION_LENGTH
    )

    if query_mode == "image" or keyword_score == 0.0:
        match_type = "visual"
    elif vector_score == 0.0 or keyword_score > vector_score:
        match_type = "caption"
    else:
        match_type = "hybrid"

    return {
        "match_type": match_type,
        "exact_phrase_match": exact_phrase_match,
        "rich_caption": rich_caption,
        "rerank_boost": round(max(0.0, rerank_score - fusion_score), 4),
    }


def rank_candidates(settings, candidates: list[dict], *, query_text: str | None, query_mode: str, limit: int) -> list[dict]:
    ranked = [{**candidate} for candidate in candidates]

    for candidate in ranked:
        vector_score = _clamp_score(candidate.get("vector_score", 0.0))
        keyword_score = _clamp_score(candidate.get("keyword_score", 0.0))
        if query_mode == "text":
            fusion_score = vector_score * settings.search_vector_weight + keyword_score * settings.search_keyword_weight
        else:
            fusion_score = vector_score
        candidate["fusion_score"] = _clamp_score(fusion_score)
        candidate["rerank_score"] = candidate["fusion_score"]

    if query_mode == "text" and query_text:
        ranked = _apply_reranking(settings, ranked, query_text)

    ranked.sort(key=lambda item: item.get("rerank_score", item.get("fusion_score", 0.0)), reverse=True)
    ranked = _apply_diversity(settings, ranked, limit, dedupe_captions=query_mode == "text")
    ranked = _calibrate_scores(ranked)
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked
