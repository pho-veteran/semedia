from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from semedia_shared.clip_service import encode_images, encode_text
from semedia_shared.config import get_settings
from semedia_shared.database import build_engine, build_session_factory, init_database, session_dependency
from semedia_shared.log import configure_logging, get_logger
from semedia_shared.media_types import infer_media_type
from semedia_shared.model_warmup import warm_models
from semedia_shared.pipeline import process_media
from semedia_shared.runtime import get_runtime_diagnostics
from semedia_shared.storage import ensure_media_root

settings = get_settings("media-worker")
configure_logging(settings)
logger = get_logger(__name__)
engine = build_engine(settings.database_url)
SessionLocal = build_session_factory(engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings)
    ensure_media_root(settings)
    init_database(engine)
    if settings.ml_preload_models:
        logger.info("Preloading caption and CLIP models before accepting traffic.")
        warm_models(settings)
    runtime = get_runtime_diagnostics(settings)
    logger.info(
        "Service startup complete. requested_device=%s selected_device=%s cuda_available=%s gpu_name=%s preload_models=%s",
        runtime["requested_device"],
        runtime["selected_device"],
        runtime["cuda_available"],
        runtime["gpu_name"] or "n/a",
        runtime["preload_models"],
    )
    yield
    logger.info("Service shutdown complete.")


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


@app.post("/internal/embeddings/image")
def embed_image(file: UploadFile = File(...)) -> dict:
    try:
        inferred_type = infer_media_type(file.filename or "query-image.bin", file.content_type or "")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    if inferred_type != "image":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="image query file is required.")

    suffix = Path(file.filename or "query-image.bin").suffix or ".bin"
    temporary_path = None

    try:
        file.file.seek(0)
        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(file.file.read())
            temporary_path = temporary_file.name

        try:
            from PIL import Image
        except Exception:
            Image = None

        if Image is not None:
            try:
                with Image.open(temporary_path) as image:
                    image.convert("RGB")
            except Exception as exc:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"invalid image query file: {exc}") from exc

        embeddings = encode_images(settings, [temporary_path])
        if not embeddings:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="image embedding generation returned no vectors.")
        return {"embedding": embeddings[0]}
    finally:
        if temporary_path is not None:
            try:
                Path(temporary_path).unlink(missing_ok=True)
            except Exception:
                pass


@app.post("/internal/media/{media_id}/process")
def process(media_id: int, session: Session = Depends(get_db)) -> dict:
    logger.info("Process request received for media %s.", media_id)
    ok = process_media(settings, session, media_id)
    if not ok:
        logger.warning("Processing request failed for media %s.", media_id)
    return {"media_id": media_id, "success": ok}
