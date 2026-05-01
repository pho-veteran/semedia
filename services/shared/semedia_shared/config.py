from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    service_name: str
    database_url: str
    media_root: Path
    media_base_url: str
    log_level: str
    log_format: str
    clip_model_name: str
    caption_model_name: str
    scene_detection_threshold: float
    search_vector_weight: float
    search_keyword_weight: float
    search_max_results: int
    ml_device: str
    ml_strict_cuda: bool
    ml_preload_models: bool
    media_worker_url: str
    search_api_url: str
    allow_all_origins: bool
    caption_max_length: int = 50
    caption_min_length: int = 10
    caption_num_beams: int = 5
    caption_retry_weak: bool = True
    caption_retry_num_beams: int = 8
    caption_batch_size: int = 8
    caption_retry_fallback: str = "Image content unclear."
    caption_weak_min_words: int = 3
    caption_weak_min_chars: int = 10
    caption_retry_max_length: int = 60
    caption_retry_min_length: int = 15


def _truthy(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def get_settings(service_name: str) -> Settings:
    media_root = Path(os.getenv("MEDIA_ROOT", "/app/storage"))
    return Settings(
        service_name=service_name,
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/semedia",
        ),
        media_root=media_root,
        media_base_url=os.getenv("MEDIA_BASE_URL", "/media").rstrip("/") or "/media",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "text").strip().lower() or "text",
        clip_model_name=os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32"),
        caption_model_name=os.getenv("CAPTION_MODEL_NAME", "Salesforce/blip-image-captioning-base"),
        scene_detection_threshold=float(os.getenv("SCENE_DETECTION_THRESHOLD", "27.0")),
        search_vector_weight=float(os.getenv("SEARCH_VECTOR_WEIGHT", "0.7")),
        search_keyword_weight=float(os.getenv("SEARCH_KEYWORD_WEIGHT", "0.3")),
        search_max_results=int(os.getenv("SEARCH_MAX_RESULTS", "20")),
        ml_device=os.getenv("ML_DEVICE", "auto").strip().lower() or "auto",
        ml_strict_cuda=_truthy("ML_STRICT_CUDA"),
        ml_preload_models=_truthy("ML_PRELOAD_MODELS", "1"),
        media_worker_url=os.getenv("MEDIA_WORKER_URL", "http://media-worker:8000").rstrip("/"),
        search_api_url=os.getenv("SEARCH_API_URL", "http://search-api:8000").rstrip("/"),
        allow_all_origins=_truthy("CORS_ALLOW_ALL_ORIGINS", "1"),
        caption_max_length=int(os.getenv("CAPTION_MAX_LENGTH", "50")),
        caption_min_length=int(os.getenv("CAPTION_MIN_LENGTH", "10")),
        caption_num_beams=int(os.getenv("CAPTION_NUM_BEAMS", "5")),
        caption_retry_weak=_truthy("CAPTION_RETRY_WEAK", "1"),
        caption_retry_num_beams=int(os.getenv("CAPTION_RETRY_NUM_BEAMS", "8")),
        caption_batch_size=int(os.getenv("CAPTION_BATCH_SIZE", "8")),
        caption_retry_fallback=os.getenv("CAPTION_RETRY_FALLBACK", "Image content unclear."),
        caption_weak_min_words=int(os.getenv("CAPTION_WEAK_MIN_WORDS", "3")),
        caption_weak_min_chars=int(os.getenv("CAPTION_WEAK_MIN_CHARS", "10")),
        caption_retry_max_length=int(os.getenv("CAPTION_RETRY_MAX_LENGTH", "60")),
        caption_retry_min_length=int(os.getenv("CAPTION_RETRY_MIN_LENGTH", "15")),
    )
