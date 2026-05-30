from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_CROSS_ENCODER = None
_CROSS_ENCODER_NAME: str | None = None


def _get_cross_encoder(settings):
    global _CROSS_ENCODER, _CROSS_ENCODER_NAME
    from sentence_transformers import CrossEncoder

    from .runtime import get_inference_device

    name = settings.rerank_model_name
    if _CROSS_ENCODER is None or _CROSS_ENCODER_NAME != name:
        device = get_inference_device(settings)
        logger.info("Loading cross-encoder %s on %s.", name, device)
        _CROSS_ENCODER = CrossEncoder(name, device=device)
        _CROSS_ENCODER_NAME = name
    return _CROSS_ENCODER


def rerank_scores(settings, query: str, texts: list[str]) -> list[float]:
    """Cross-encoder relevance of *query* vs each text, sigmoid-normalized to [0,1]."""
    if not texts:
        return []
    import numpy as np

    raw = _get_cross_encoder(settings).predict([(query, text or "") for text in texts])
    return [float(1.0 / (1.0 + np.exp(-float(score)))) for score in raw]
