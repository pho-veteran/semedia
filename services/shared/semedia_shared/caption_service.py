from __future__ import annotations

import logging
from typing import Iterable

from .fallback_ai import caption_from_path
from .hf_loader import load_pretrained_model
from .runtime import ensure_cuda_ready, get_inference_device, is_strict_cuda_mode, release_torch_memory

logger = logging.getLogger(__name__)


def _load_processor(processor_class, model_name: str):
    try:
        return processor_class.from_pretrained(model_name, use_fast=True)
    except Exception as exc:
        logger.info("Falling back to the default processor for %s: %s", model_name, exc)
        return processor_class.from_pretrained(model_name)


def generate_captions(settings, image_paths: Iterable[str]) -> list[str]:
    image_paths = list(image_paths)
    if not image_paths:
        return []

    try:
        import torch
        from PIL import Image
        from transformers import (
            BitsAndBytesConfig,
            Blip2ForConditionalGeneration,
            Blip2Processor,
            BlipForConditionalGeneration,
            BlipProcessor,
        )
    except Exception:
        return [caption_from_path(path) for path in image_paths]

    model_name = settings.caption_model_name
    model_name_lower = model_name.lower()
    device = get_inference_device(settings)
    strict_cuda = is_strict_cuda_mode(settings)
    model = None
    processor = None
    use_device_map = False

    try:
        if strict_cuda and device == "cuda":
            ensure_cuda_ready(settings)

        is_blip2 = "blip2" in model_name_lower
        processor_class = Blip2Processor if is_blip2 else BlipProcessor
        model_class = Blip2ForConditionalGeneration if is_blip2 else BlipForConditionalGeneration
        processor = _load_processor(processor_class, model_name)
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

        model, use_device_map = load_pretrained_model(
            model_class=model_class,
            model_name=model_name,
            device=device,
            load_attempts=load_attempts,
            release_memory=release_torch_memory,
            log_label=f"Caption model {model_name}",
        )
        model.eval()
        logger.info("Running caption inference with %s on %s.", model_name, device)

        captions: list[str] = []
        with torch.inference_mode():
            for image_path in image_paths:
                image = Image.open(image_path).convert("RGB")
                inputs = processor(images=image, return_tensors="pt", input_data_format="channels_last")
                if device != "cuda" or not use_device_map:
                    inputs = {key: value.to(device) for key, value in inputs.items()}
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
