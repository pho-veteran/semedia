from __future__ import annotations

import logging
from collections.abc import Iterable

from . import caption_cleanup_config as cleanup_config
from .fallback_ai import caption_from_path
from .hf_loader import load_cached_pretrained_model, load_pretrained_processor
from .ml_inputs import build_image_inputs, move_batch_to_device
from .runtime import ensure_cuda_ready, get_inference_device, is_strict_cuda_mode, release_torch_memory

logger = logging.getLogger(__name__)

_GENERIC_CAPTION_PATTERNS = tuple(cleanup_config.GENERIC_EXACT)
_CLEANUP_STRIP = ".,;: "
_CLEANUP_SPACE = " "
_CLEANUP_DOUBLE_SPACE = "  "
_CLEANUP = {
    "rules": cleanup_config.REWRITE_PREFIXES + cleanup_config.REWRITE_FRAGMENTS + cleanup_config.REWRITE_SUFFIXES,
    "patterns": tuple(cleanup_config.GENERIC_EXACT) + ("a close up of", "close up of"),
    "hints": cleanup_config.USEFUL_TERMS,
    "min_words": cleanup_config.MIN_WORDS,
    "bad_exact": cleanup_config.GENERIC_EXACT | {"image content unclear"},
    "bad_tokens": cleanup_config.MALFORMED_TOKENS,
    "trivial": frozenset({"red", "white", "background", "border"}),
    "fallback": cleanup_config.FALLBACK_CAPTION,
}


def _normalize_caption_signal(caption: str) -> str:
    lowered = caption.lower().strip(_CLEANUP_STRIP)
    for noisy in _CLEANUP["bad_tokens"]:
        lowered = lowered.replace(noisy, "")
    for old, new in _CLEANUP["rules"]:
        lowered = lowered.replace(old, new)
    while _CLEANUP_DOUBLE_SPACE in lowered:
        lowered = lowered.replace(_CLEANUP_DOUBLE_SPACE, _CLEANUP_SPACE)
    return lowered.strip(_CLEANUP_STRIP)


def _clean_caption(caption: str) -> str:
    if not caption:
        return ""

    normalized = _normalize_caption_signal(caption)
    if not normalized:
        return ""

    cleaned = normalized[0].upper() + normalized[1:]
    if cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


def _is_weak_caption(settings, caption: str) -> bool:
    if not settings.caption_enable_weak_filtering:
        return False

    cleaned = caption.strip()
    if len(cleaned) < settings.caption_weak_min_chars:
        return True

    lowered = cleaned.lower()
    if any(pattern in lowered for pattern in _GENERIC_CAPTION_PATTERNS):
        return True

    return len(cleaned.split()) < settings.caption_weak_min_words


def _generate_batch_captions(image_module, processor, model, device: str, use_device_map: bool, image_paths: list[str], generation_kwargs: dict[str, int | float]) -> list[str]:
    images = [image_module.open(path).convert("RGB") for path in image_paths]
    inputs = build_image_inputs(processor, images)
    if device != "cuda" or not use_device_map:
        inputs = move_batch_to_device(inputs, device)
    output_ids = model.generate(**inputs, **generation_kwargs)
    return processor.batch_decode(output_ids, skip_special_tokens=True)


def _base_generation_kwargs(settings) -> dict[str, int | float]:
    return {
        "max_length": settings.caption_max_length,
        "min_length": settings.caption_min_length,
        "num_beams": settings.caption_num_beams,
        "length_penalty": 0.8,
        "repetition_penalty": 1.2,
        "no_repeat_ngram_size": 3,
    }


def _retry_generation_kwargs(settings) -> dict[str, int | float]:
    return {
        "max_length": settings.caption_retry_max_length,
        "min_length": settings.caption_retry_min_length,
        "num_beams": settings.caption_retry_num_beams,
        "length_penalty": 1.0,
        "repetition_penalty": 1.5,
        "no_repeat_ngram_size": 2,
    }


def _chunk_paths(image_paths: list[str], batch_size: int) -> Iterable[list[str]]:
    for i in range(0, len(image_paths), batch_size):
        yield image_paths[i : i + batch_size]


def _fallback_captions(image_paths: list[str]) -> list[str]:
    return [_clean_caption(caption_from_path(path)) for path in image_paths]


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
        torch, image_module, model_name, device, strict_cuda, processor, model, use_device_map = _load_caption_resources(settings)
    except Exception as exc:
        if strict_cuda and device == "cuda":
            raise RuntimeError(f"Strict CUDA caption inference failed: {exc}") from exc
        return _fallback_captions(image_paths)

    try:
        logger.info("Running caption inference with %s on %s.", model_name, device)

        captions: list[str] = []
        retry_paths: list[str] = []
        retry_indices: list[int] = []
        batch_size = settings.caption_batch_size
        base_kwargs = _base_generation_kwargs(settings)
        retry_kwargs = _retry_generation_kwargs(settings)

        with torch.inference_mode():
            for batch_paths in _chunk_paths(image_paths, batch_size):
                batch_captions = _generate_batch_captions(
                    image_module,
                    processor,
                    model,
                    device,
                    use_device_map,
                    batch_paths,
                    base_kwargs,
                )
                for path, raw_caption in zip(batch_paths, batch_captions):
                    cleaned = _clean_caption(raw_caption)
                    if settings.caption_retry_weak and _is_weak_caption(settings, cleaned):
                        retry_indices.append(len(captions))
                        retry_paths.append(path)
                        captions.append("")
                    else:
                        captions.append(cleaned)

            if retry_paths:
                logger.info("Retrying %d weak captions with stricter settings.", len(retry_paths))
                for batch_paths in _chunk_paths(retry_paths, batch_size):
                    batch_retry_captions = _generate_batch_captions(
                        image_module,
                        processor,
                        model,
                        device,
                        use_device_map,
                        batch_paths,
                        retry_kwargs,
                    )
                    for raw_caption in batch_retry_captions:
                        retry_index = retry_indices.pop(0)
                        cleaned = _clean_caption(raw_caption)
                        if cleaned and not _is_weak_caption(settings, cleaned):
                            captions[retry_index] = cleaned
                        else:
                            captions[retry_index] = settings.caption_retry_fallback

        return captions
    except Exception as exc:
        if strict_cuda and device == "cuda":
            raise RuntimeError(f"Strict CUDA caption inference failed: {exc}") from exc
        logger.warning("Caption model unavailable, falling back to deterministic captions: %s", exc)
        return _fallback_captions(image_paths)
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
