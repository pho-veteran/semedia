from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import requests
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from semedia_shared.config import get_settings
from semedia_shared.database import build_engine, build_session_factory, init_database, session_dependency
from semedia_shared.log import configure_logging, get_logger
from semedia_shared.media_types import infer_media_type, validate_media_type
from semedia_shared.models import MediaItem, ProcessingStatus
from semedia_shared.serialization import media_detail, media_summary
from semedia_shared.storage import delete_media_files, ensure_media_root, save_upload

settings = get_settings("gateway-api")
configure_logging(settings)
logger = get_logger(__name__)
engine = build_engine(settings.database_url)
SessionLocal = build_session_factory(engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings)
    ensure_media_root(settings)
    init_database(engine)
    logger.info("Service startup complete.")
    yield
    logger.info("Service shutdown complete.")


app = FastAPI(title="Semedia Gateway API", version="0.1.0", lifespan=lifespan)
app.mount(settings.media_base_url, StaticFiles(directory=settings.media_root, check_dir=False), name="media")

if settings.allow_all_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_db():
    yield from session_dependency(SessionLocal)


def _trigger_worker_processing(media_id: int) -> None:
    session = SessionLocal()
    try:
        response = requests.post(
            f"{settings.media_worker_url}/internal/media/{media_id}/process",
            timeout=3600,
        )
        response.raise_for_status()
    except Exception as exc:
        logger.exception("Worker dispatch failed for media %s.", media_id)
        media = session.get(MediaItem, media_id)
        if media is not None and media.status in {ProcessingStatus.PENDING, ProcessingStatus.PROCESSING}:
            media.status = ProcessingStatus.FAILED
            media.error_message = f"Worker dispatch failed: {exc}"
            media.updated_at = datetime.now(timezone.utc)
            session.commit()
    finally:
        session.close()


def _proxy_worker_runtime() -> dict:
    try:
        response = requests.get(f"{settings.media_worker_url}/internal/runtime", timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.exception("Runtime status proxy failed.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Media worker unavailable: {exc}") from exc


@app.get("/api/v1/health/")
def health() -> dict:
    return {"status": "healthy", "service": settings.service_name, "phase": "microservices-mvp"}


@app.get("/api/v1/runtime/")
def runtime_status() -> dict:
    return _proxy_worker_runtime()


@app.post("/api/v1/media/upload/", status_code=status.HTTP_201_CREATED)
def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    media_type: str | None = Form(default=None),
    session: Session = Depends(get_db),
) -> dict:
    inferred_type = infer_media_type(file.filename or "upload.bin", file.content_type or "")
    if media_type:
        validate_media_type(media_type, inferred_type, file.filename or "upload.bin")
    selected_media_type = media_type or inferred_type

    relative_path, file_size = save_upload(settings, file)
    media = MediaItem(
        file_path=relative_path,
        original_filename=file.filename or "upload.bin",
        media_type=selected_media_type,
        mime_type=file.content_type or "",
        file_size=file_size,
        status=ProcessingStatus.PENDING,
        enqueued_at=datetime.now(timezone.utc),
    )
    session.add(media)
    session.commit()
    session.refresh(media)
    background_tasks.add_task(_trigger_worker_processing, media.id)

    media = session.execute(
        select(MediaItem).options(selectinload(MediaItem.scenes)).where(MediaItem.id == media.id)
    ).scalar_one()

    return {
        "message": "Media queued for worker processing.",
        "processing_enqueued": True,
        "dispatch_backend": "http",
        "data": media_summary(settings, media),
    }


@app.get("/api/v1/media/")
def list_media(
    media_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    session: Session = Depends(get_db),
) -> dict:
    statement = select(MediaItem).options(selectinload(MediaItem.scenes)).order_by(desc(MediaItem.uploaded_at))
    if media_type:
        statement = statement.where(MediaItem.media_type == media_type)
    if status_filter:
        statement = statement.where(MediaItem.status == status_filter)

    items = list(session.execute(statement).scalars())
    return {
        "count": len(items),
        "next": None,
        "previous": None,
        "results": [media_summary(settings, item) for item in items],
    }


@app.get("/api/v1/media/{media_id}/")
def get_media_detail(media_id: int, session: Session = Depends(get_db)) -> dict:
    media = session.execute(
        select(MediaItem).options(selectinload(MediaItem.scenes)).where(MediaItem.id == media_id)
    ).scalar_one_or_none()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    return media_detail(settings, media)


@app.delete("/api/v1/media/{media_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(media_id: int, session: Session = Depends(get_db)) -> None:
    media = session.execute(
        select(MediaItem).options(selectinload(MediaItem.scenes)).where(MediaItem.id == media_id)
    ).scalar_one_or_none()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    delete_media_files(settings, media)
    session.delete(media)
    session.commit()


@app.post("/api/v1/search/")
def search(payload: dict) -> dict:
    try:
        response = requests.post(f"{settings.search_api_url}/api/v1/search/", json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        logger.warning("Search API returned an error response: %s", exc)
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(status_code=exc.response.status_code if exc.response is not None else 502, detail=detail) from exc
    except Exception as exc:
        logger.exception("Search API request failed.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Search API unavailable: {exc}") from exc
