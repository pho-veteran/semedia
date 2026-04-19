from __future__ import annotations

from time import perf_counter

from .caption_service import warm_caption_model
from .clip_service import warm_clip_model
from .log import get_logger

logger = get_logger(__name__)


def warm_models(settings) -> dict[str, float]:
    total_started = perf_counter()

    caption_started = perf_counter()
    warm_caption_model(settings)
    caption_seconds = perf_counter() - caption_started

    clip_started = perf_counter()
    warm_clip_model(settings)
    clip_seconds = perf_counter() - clip_started

    total_seconds = perf_counter() - total_started
    logger.info(
        "Model warm-up complete. caption_seconds=%.2f clip_seconds=%.2f total_seconds=%.2f",
        caption_seconds,
        clip_seconds,
        total_seconds,
    )
    return {
        "caption_seconds": caption_seconds,
        "clip_seconds": clip_seconds,
        "total_seconds": total_seconds,
    }
