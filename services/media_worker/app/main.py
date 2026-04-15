from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from semedia_shared.clip_service import encode_text
from semedia_shared.config import get_settings
from semedia_shared.database import build_engine, build_session_factory, init_database, session_dependency
from semedia_shared.pipeline import process_media
from semedia_shared.runtime import get_runtime_diagnostics
from semedia_shared.storage import ensure_media_root

settings = get_settings("media-worker")
engine = build_engine(settings.database_url)
SessionLocal = build_session_factory(engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_media_root(settings)
    init_database(engine)
    yield


app = FastAPI(title="Semedia Media Worker", version="0.1.0", lifespan=lifespan)


def get_db():
    yield from session_dependency(SessionLocal)


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "service": settings.service_name}


@app.get("/internal/runtime")
def runtime_status() -> dict:
    return get_runtime_diagnostics(settings)


@app.post("/internal/embeddings/text")
def embed_text(payload: dict) -> dict:
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="text is required.")
    return {"embedding": encode_text(settings, text)}


@app.post("/internal/media/{media_id}/process")
def process(media_id: int, session: Session = Depends(get_db)) -> dict:
    ok = process_media(settings, session, media_id)
    return {"media_id": media_id, "success": ok}
