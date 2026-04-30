from __future__ import annotations

import gzip
import pickle
from dataclasses import dataclass
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from .log import get_logger
from .models import KeywordIndexArtifact, MediaItem, ProcessingStatus
from .storage import media_url

logger = get_logger(__name__)

ARTIFACT_KEY = "default"
FORMAT_VERSION = "v1"

_cached_index: KeywordIndexData | None = None
_cached_metadata: tuple[datetime, str, int, bytes | None] | None = None


@dataclass
class KeywordIndexData:
    vectorizer: TfidfVectorizer
    tfidf_matrix: any
    payloads: list[dict]
    document_count: int
    format_version: str
    built_at: datetime


def _completed_media(session: Session) -> list[MediaItem]:
    from sqlalchemy.orm import selectinload

    return list(
        session.execute(
            select(MediaItem)
            .options(selectinload(MediaItem.scenes))
            .where(MediaItem.status == ProcessingStatus.COMPLETED)
        ).scalars()
    )


def build_keyword_index(settings, session: Session) -> KeywordIndexData | None:
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
        return None

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)
    tfidf_matrix = vectorizer.fit_transform(corpus)

    return KeywordIndexData(
        vectorizer=vectorizer,
        tfidf_matrix=tfidf_matrix,
        payloads=payloads,
        document_count=len(corpus),
        format_version=FORMAT_VERSION,
        built_at=datetime.utcnow(),
    )


def serialize_index(index_data: KeywordIndexData) -> bytes:
    payload = {
        "vectorizer": index_data.vectorizer,
        "tfidf_matrix": index_data.tfidf_matrix,
        "payloads": index_data.payloads,
        "document_count": index_data.document_count,
        "format_version": index_data.format_version,
        "built_at": index_data.built_at,
    }
    return gzip.compress(pickle.dumps(payload))


def deserialize_index(payload: bytes) -> KeywordIndexData:
    data = pickle.loads(gzip.decompress(payload))
    return KeywordIndexData(
        vectorizer=data["vectorizer"],
        tfidf_matrix=data["tfidf_matrix"],
        payloads=data["payloads"],
        document_count=data["document_count"],
        format_version=data["format_version"],
        built_at=data["built_at"],
    )


def persist_keyword_index(session: Session, index_data: KeywordIndexData) -> None:
    artifact = session.execute(
        select(KeywordIndexArtifact).where(KeywordIndexArtifact.artifact_key == ARTIFACT_KEY)
    ).scalar_one_or_none()

    serialized = serialize_index(index_data)

    if artifact:
        artifact.format_version = index_data.format_version
        artifact.document_count = index_data.document_count
        artifact.payload = serialized
        artifact.built_at = index_data.built_at
        artifact.updated_at = datetime.utcnow()
    else:
        artifact = KeywordIndexArtifact(
            artifact_key=ARTIFACT_KEY,
            format_version=index_data.format_version,
            document_count=index_data.document_count,
            payload=serialized,
            built_at=index_data.built_at,
        )
        session.add(artifact)

    session.commit()


def load_keyword_index(session: Session) -> KeywordIndexData | None:
    artifact = session.execute(
        select(KeywordIndexArtifact).where(KeywordIndexArtifact.artifact_key == ARTIFACT_KEY)
    ).scalar_one_or_none()

    if not artifact or not artifact.payload:
        return None

    try:
        return deserialize_index(artifact.payload)
    except Exception as exc:
        logger.exception("Failed to deserialize keyword index artifact")
        return None


def rebuild_keyword_index(settings, session: Session) -> None:
    index_data = build_keyword_index(settings, session)
    if index_data:
        persist_keyword_index(session, index_data)
        logger.info("Keyword index rebuilt: %d documents", index_data.document_count)
    else:
        artifact = session.execute(
            select(KeywordIndexArtifact).where(KeywordIndexArtifact.artifact_key == ARTIFACT_KEY)
        ).scalar_one_or_none()
        if artifact:
            artifact.document_count = 0
            artifact.payload = None
            artifact.updated_at = datetime.utcnow()
            session.commit()
        logger.info("Keyword index rebuilt: 0 documents (empty corpus)")


def search_keyword(query_text: str, index_data: KeywordIndexData, top_k: int) -> list[dict]:
    query_vec = index_data.vectorizer.transform([query_text])
    similarities = cosine_similarity(query_vec, index_data.tfidf_matrix).flatten()

    results: list[dict] = []
    for index, similarity in enumerate(similarities):
        if similarity <= 0:
            continue
        results.append({**index_data.payloads[index], "score": float(similarity)})

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: max(top_k * 2, top_k)]


def ensure_keyword_index_current(settings, session: Session) -> KeywordIndexData | None:
    global _cached_index, _cached_metadata

    artifact = session.execute(
        select(KeywordIndexArtifact).where(KeywordIndexArtifact.artifact_key == ARTIFACT_KEY)
    ).scalar_one_or_none()

    if not artifact:
        logger.info("Keyword index artifact missing, building now")
        rebuild_keyword_index(settings, session)
        artifact = session.execute(
            select(KeywordIndexArtifact).where(KeywordIndexArtifact.artifact_key == ARTIFACT_KEY)
        ).scalar_one_or_none()
        if not artifact or not artifact.payload:
            return None

    current_metadata = (
        artifact.updated_at,
        artifact.format_version,
        artifact.document_count,
        artifact.payload,
    )

    if _cached_index and _cached_metadata == current_metadata:
        return _cached_index

    if artifact.format_version != FORMAT_VERSION:
        logger.warning("Keyword index format version mismatch, rebuilding")
        rebuild_keyword_index(settings, session)
        artifact = session.execute(
            select(KeywordIndexArtifact).where(KeywordIndexArtifact.artifact_key == ARTIFACT_KEY)
        ).scalar_one_or_none()
        if not artifact or not artifact.payload:
            return None

    if not artifact.payload:
        return None

    try:
        _cached_index = deserialize_index(artifact.payload)
        _cached_metadata = (
            artifact.updated_at,
            artifact.format_version,
            artifact.document_count,
            artifact.payload,
        )
        logger.debug("Keyword index loaded from cache: %d documents", _cached_index.document_count)
        return _cached_index
    except Exception as exc:
        logger.exception("Failed to load keyword index, rebuilding")
        rebuild_keyword_index(settings, session)
        artifact = session.execute(
            select(KeywordIndexArtifact).where(KeywordIndexArtifact.artifact_key == ARTIFACT_KEY)
        ).scalar_one_or_none()
        if not artifact or not artifact.payload:
            return None
        _cached_index = deserialize_index(artifact.payload)
        _cached_metadata = (
            artifact.updated_at,
            artifact.format_version,
            artifact.document_count,
            artifact.payload,
        )
        return _cached_index
