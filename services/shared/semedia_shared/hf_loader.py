from __future__ import annotations

import logging
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)


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
