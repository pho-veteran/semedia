from __future__ import annotations

from contextlib import asynccontextmanager

import requests
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from semedia_shared.config import get_settings
from semedia_shared.database import build_engine, build_session_factory, init_database, session_dependency
from semedia_shared.log import configure_logging, get_logger
from semedia_shared.search_service import search_text

settings = get_settings("search-api")
configure_logging(settings)
logger = get_logger(__name__)
engine = build_engine(settings.database_url)
SessionLocal = build_session_factory(engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings)
    init_database(engine)
    logger.info("Service startup complete.")
    yield
    logger.info("Service shutdown complete.")


app = FastAPI(title="Semedia Search API", version="0.1.0", lifespan=lifespan)

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


def _embed_text(query_text: str) -> list[float]:
    try:
        response = requests.post(
            f"{settings.media_worker_url}/internal/embeddings/text",
            json={"text": query_text},
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["embedding"]
    except Exception as exc:
        logger.exception("Text embedding request failed.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Media worker unavailable: {exc}") from exc


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "service": settings.service_name}


@app.post("/api/v1/search/")
def search(payload: dict, session: Session = Depends(get_db)) -> dict:
    query_text = (payload.get("query_text") or "").strip()
    if not query_text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="query_text is required.")

    top_k = payload.get("top_k")
    if top_k is not None:
        try:
            top_k = int(top_k)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="top_k must be an integer.") from exc

    query_embedding = _embed_text(query_text)
    results = search_text(settings, session, query_text, query_embedding, top_k=top_k)
    return {"query_text": query_text, "count": len(results), "results": results}
