from __future__ import annotations

import logging
from typing import Iterable

from .fallback_ai import embedding_from_path, embedding_from_text
from .hf_loader import load_cached_pretrained_model, load_pretrained_processor
from .ml_inputs import build_image_inputs, move_batch_to_device
from .runtime import ensure_cuda_ready, get_inference_device, is_strict_cuda_mode, release_torch_memory

logger = logging.getLogger(__name__)


def _normalize(vector):
    norm = vector.norm(p=2, dim=-1, keepdim=True)
    return vector / norm


def _load_clip_resources(settings):
    import torch
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor

    device = get_inference_device(settings)
    strict_cuda = is_strict_cuda_mode(settings)
    model_name = settings.clip_model_name

    if strict_cuda and device == "cuda":
        ensure_cuda_ready(settings)

    if device == "cuda":
        load_attempts = [
            ({"dtype": torch.float16, "low_cpu_mem_usage": False}, False),
            ({"dtype": torch.float16, "device_map": {"": device}}, True),
        ]
    else:
        load_attempts = [({"dtype": torch.float32, "low_cpu_mem_usage": False}, False)]

    model, use_device_map = load_cached_pretrained_model(
        model_class=CLIPModel,
        model_name=model_name,
        device=device,
        load_attempts=load_attempts,
        release_memory=release_torch_memory,
        log_label=f"CLIP model {model_name}",
    )
    processor = load_pretrained_processor(processor_class=CLIPProcessor, model_name=model_name)
    model.eval()

    return torch, Image, model_name, device, strict_cuda, processor, model, use_device_map


def encode_images(settings, image_paths: Iterable[str]) -> list[list[float]]:
    image_paths = list(image_paths)
    if not image_paths:
        return []

    device = get_inference_device(settings)
    strict_cuda = is_strict_cuda_mode(settings)
    model_name = settings.clip_model_name
    model = None
    processor = None

    try:
        torch, Image, model_name, device, strict_cuda, processor, model, use_device_map = _load_clip_resources(settings)
        logger.info("Running CLIP image inference with %s on %s.", model_name, device)
        embeddings: list[list[float]] = []
        with torch.inference_mode():
            for image_path in image_paths:
                image = Image.open(image_path).convert("RGB")
                inputs = build_image_inputs(processor, image)
                if device != "cuda" or not use_device_map:
                    inputs = move_batch_to_device(inputs, device)
                features = model.get_image_features(**inputs)
                embeddings.append(_normalize(features).squeeze(0).cpu().tolist())
        return embeddings
    except Exception as exc:
        if strict_cuda and device == "cuda":
            raise RuntimeError(f"Strict CUDA CLIP image inference failed: {exc}") from exc
        logger.warning("CLIP image inference unavailable, falling back to deterministic embeddings: %s", exc)
        return [embedding_from_path(path) for path in image_paths]
    finally:
        try:
            del model
            del processor
        except Exception:
            pass
        release_torch_memory()


def encode_text(settings, text: str) -> list[float]:
    device = get_inference_device(settings)
    strict_cuda = is_strict_cuda_mode(settings)
    model_name = settings.clip_model_name
    model = None
    processor = None

    try:
        torch, _Image, model_name, device, strict_cuda, processor, model, use_device_map = _load_clip_resources(settings)
        logger.info("Running CLIP text inference with %s on %s.", model_name, device)
        with torch.inference_mode():
            inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
            if device != "cuda" or not use_device_map:
                inputs = move_batch_to_device(inputs, device)
            features = model.get_text_features(**inputs)
            return _normalize(features).squeeze(0).cpu().tolist()
    except Exception as exc:
        if strict_cuda and device == "cuda":
            raise RuntimeError(f"Strict CUDA CLIP text inference failed: {exc}") from exc
        logger.warning("CLIP text inference unavailable, falling back to deterministic embeddings: %s", exc)
        return embedding_from_text(text)
    finally:
        try:
            del model
            del processor
        except Exception:
            pass
        release_torch_memory()


def warm_clip_model(settings) -> None:
    model_name = settings.clip_model_name
    device = get_inference_device(settings)
    model = None
    processor = None

    try:
        torch, Image, model_name, device, _strict_cuda, processor, model, use_device_map = _load_clip_resources(settings)
        logger.info("Running CLIP warm-up with %s on %s.", model_name, device)

        with torch.inference_mode():
            image = Image.new("RGB", (32, 32), color=(0, 0, 0))
            image_inputs = build_image_inputs(processor, image)
            if device != "cuda" or not use_device_map:
                image_inputs = move_batch_to_device(image_inputs, device)
            model.get_image_features(**image_inputs)

            text_inputs = processor(text=["startup probe"], return_tensors="pt", padding=True, truncation=True)
            if device != "cuda" or not use_device_map:
                text_inputs = move_batch_to_device(text_inputs, device)
            model.get_text_features(**text_inputs)
    except Exception as exc:
        raise RuntimeError(f"CLIP warm-up failed for {model_name} on {device}: {exc}") from exc
    finally:
        try:
            del model
            del processor
        except Exception:
            pass
        release_torch_memory()
