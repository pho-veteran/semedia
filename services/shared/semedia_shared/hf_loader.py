from __future__ import annotations

import logging
from threading import Lock
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)
_MODEL_CACHE: dict[tuple[str, str, str], tuple[Any, bool]] = {}
_PROCESSOR_CACHE: dict[tuple[str, str], Any] = {}
_CACHE_LOCK = Lock()


def _class_cache_key(class_object: Any) -> str:
    return f"{class_object.__module__}.{class_object.__name__}"


def model_has_meta_tensors(model: Any) -> bool:
    for tensor in model.parameters():
        if getattr(tensor, "is_meta", False):
            return True
    for tensor in model.buffers():
        if getattr(tensor, "is_meta", False):
            return True
    return False


def load_pretrained_model(
    *,
    model_class: Any,
    model_name: str,
    device: str,
    load_attempts: Iterable[tuple[dict[str, Any], bool]],
    release_memory: Callable[[], None],
    log_label: str,
) -> tuple[Any, bool]:
    last_error: Exception | None = None

    for load_kwargs, use_device_map in load_attempts:
        try:
            model = model_class.from_pretrained(model_name, **load_kwargs)
            if not use_device_map:
                if model_has_meta_tensors(model):
                    raise RuntimeError(
                        "Model weights are still on meta tensors after load. "
                        "Refusing to call .to(device) on an unmaterialized model."
                    )
                model = model.to(device)
            return model, use_device_map
        except Exception as exc:
            last_error = exc
            logger.warning(
                "%s load attempt failed with kwargs %s: %s",
                log_label,
                sorted(load_kwargs.keys()),
                exc,
            )
            release_memory()

    if last_error is None:
        raise RuntimeError(f"{log_label} did not receive any load attempts.")

    raise RuntimeError(f"{log_label} could not be loaded on {device}: {last_error}") from last_error


def load_cached_pretrained_model(
    *,
    model_class: Any,
    model_name: str,
    device: str,
    load_attempts: Iterable[tuple[dict[str, Any], bool]],
    release_memory: Callable[[], None],
    log_label: str,
) -> tuple[Any, bool]:
    cache_key = (_class_cache_key(model_class), model_name, device)
    with _CACHE_LOCK:
        cached = _MODEL_CACHE.get(cache_key)
    if cached is not None:
        return cached

    loaded = load_pretrained_model(
        model_class=model_class,
        model_name=model_name,
        device=device,
        load_attempts=load_attempts,
        release_memory=release_memory,
        log_label=log_label,
    )

    with _CACHE_LOCK:
        existing = _MODEL_CACHE.get(cache_key)
        if existing is not None:
            return existing
        _MODEL_CACHE[cache_key] = loaded

    logger.info("%s cached for device %s.", log_label, device)
    return loaded


def load_pretrained_processor(*, processor_class: Any, model_name: str) -> Any:
    cache_key = (_class_cache_key(processor_class), model_name)
    with _CACHE_LOCK:
        cached = _PROCESSOR_CACHE.get(cache_key)
    if cached is not None:
        return cached

    try:
        processor = processor_class.from_pretrained(model_name, use_fast=True)
    except Exception as exc:
        logger.info("Falling back to the default processor for %s: %s", model_name, exc)
        processor = processor_class.from_pretrained(model_name)

    with _CACHE_LOCK:
        existing = _PROCESSOR_CACHE.get(cache_key)
        if existing is not None:
            return existing
        _PROCESSOR_CACHE[cache_key] = processor

    return processor


def clear_pretrained_caches() -> None:
    with _CACHE_LOCK:
        _MODEL_CACHE.clear()
        _PROCESSOR_CACHE.clear()
