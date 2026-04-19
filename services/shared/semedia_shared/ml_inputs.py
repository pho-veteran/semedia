from __future__ import annotations

from typing import Any


def build_image_inputs(processor: Any, image: Any) -> Any:
    return processor(images=image, return_tensors="pt")


def move_batch_to_device(inputs: Any, device: str) -> Any:
    if hasattr(inputs, "to"):
        return inputs.to(device)

    return {key: value.to(device) for key, value in inputs.items()}
