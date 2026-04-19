from __future__ import annotations

import logging
from typing import Iterable

from .fallback_ai import caption_from_path
from .hf_loader import load_cached_pretrained_model, load_pretrained_processor
from .ml_inputs import build_image_inputs, move_batch_to_device
from .runtime import ensure_cuda_ready, get_inference_device, is_strict_cuda_mode, release_torch_memory

logger = logging.getLogger(__name__)


def _load_caption_resources(settings):
    import torch
    from PIL import Image
    from transformers import (
        BitsAndBytesConfig,
        Blip2ForConditionalGeneration,
        Blip2Processor,
        BlipForConditionalGeneration,
        BlipProcessor,
    )

    model_name = settings.caption_model_name
    model_name_lower = model_name.lower()
    device = get_inference_device(settings)
    strict_cuda = is_strict_cuda_mode(settings)

    if strict_cuda and device == "cuda":
        ensure_cuda_ready(settings)

    is_blip2 = "blip2" in model_name_lower
    processor_class = Blip2Processor if is_blip2 else BlipProcessor
    model_class = Blip2ForConditionalGeneration if is_blip2 else BlipForConditionalGeneration
    processor = load_pretrained_processor(processor_class=processor_class, model_name=model_name)
    load_attempts: list[tuple[dict[str, object], bool]] = []

    if device == "cuda" and is_blip2:
        try:
            load_attempts.append(
                (
                    {
                        "quantization_config": BitsAndBytesConfig(load_in_8bit=True),
                        "device_map": {"": device},
                    },
                    True,
                )
            )
        except Exception:
            logger.warning("BitsAndBytesConfig was unavailable. Falling back to full-precision BLIP-2 loading.")
        load_attempts.append(({"dtype": torch.float16, "low_cpu_mem_usage": False}, False))
        load_attempts.append(({"dtype": torch.float16, "device_map": {"": device}}, True))
    elif device == "cuda":
        load_attempts.append(({"dtype": torch.float16, "low_cpu_mem_usage": False}, False))
        load_attempts.append(({"dtype": torch.float16, "device_map": {"": device}}, True))
    else:
        load_attempts.append(({"dtype": torch.float32, "low_cpu_mem_usage": False}, False))

    model, use_device_map = load_cached_pretrained_model(
        model_class=model_class,
        model_name=model_name,
        device=device,
        load_attempts=load_attempts,
        release_memory=release_torch_memory,
        log_label=f"Caption model {model_name}",
    )
    model.eval()

    return torch, Image, model_name, device, strict_cuda, processor, model, use_device_map


def generate_captions(settings, image_paths: Iterable[str]) -> list[str]:
    image_paths = list(image_paths)
    if not image_paths:
        return []

    model_name = settings.caption_model_name
    device = get_inference_device(settings)
    strict_cuda = is_strict_cuda_mode(settings)
    model = None
    processor = None

    try:
        torch, Image, model_name, device, strict_cuda, processor, model, use_device_map = _load_caption_resources(settings)
    except Exception as exc:
        if strict_cuda and device == "cuda":
            raise RuntimeError(f"Strict CUDA caption inference failed: {exc}") from exc
        return [caption_from_path(path) for path in image_paths]

    try:
        logger.info("Running caption inference with %s on %s.", model_name, device)

        captions: list[str] = []
        with torch.inference_mode():
            for image_path in image_paths:
                image = Image.open(image_path).convert("RGB")
                inputs = build_image_inputs(processor, image)
                if device != "cuda" or not use_device_map:
                    inputs = move_batch_to_device(inputs, device)
                output_ids = model.generate(**inputs, max_new_tokens=40)
                caption = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
                captions.append(caption)
        return captions
    except Exception as exc:
        if strict_cuda and device == "cuda":
            raise RuntimeError(f"Strict CUDA caption inference failed: {exc}") from exc
        logger.warning("Caption model unavailable, falling back to deterministic captions: %s", exc)
        return [caption_from_path(path) for path in image_paths]
    finally:
        try:
            del model
            del processor
        except Exception:
            pass
        release_torch_memory()


def warm_caption_model(settings) -> None:
    model_name = settings.caption_model_name
    device = get_inference_device(settings)
    model = None
    processor = None

    try:
        torch, Image, model_name, device, _strict_cuda, processor, model, use_device_map = _load_caption_resources(settings)
        logger.info("Running caption warm-up with %s on %s.", model_name, device)

        with torch.inference_mode():
            image = Image.new("RGB", (32, 32), color=(0, 0, 0))
            inputs = build_image_inputs(processor, image)
            if device != "cuda" or not use_device_map:
                inputs = move_batch_to_device(inputs, device)
            model.generate(**inputs, max_new_tokens=2)
    except Exception as exc:
        raise RuntimeError(f"Caption warm-up failed for {model_name} on {device}: {exc}") from exc
    finally:
        try:
            del model
            del processor
        except Exception:
            pass
        release_torch_memory()
