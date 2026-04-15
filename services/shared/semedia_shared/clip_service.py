from __future__ import annotations

import logging
from typing import Iterable

from .fallback_ai import embedding_from_path, embedding_from_text
from .hf_loader import load_pretrained_model
from .runtime import ensure_cuda_ready, get_inference_device, is_strict_cuda_mode, release_torch_memory

logger = logging.getLogger(__name__)


def _normalize(vector):
    norm = vector.norm(p=2, dim=-1, keepdim=True)
    return vector / norm


def _load_processor(processor_class, model_name: str):
    try:
        return processor_class.from_pretrained(model_name, use_fast=True)
    except Exception as exc:
        logger.info("Falling back to the default processor for %s: %s", model_name, exc)
        return processor_class.from_pretrained(model_name)


def encode_images(settings, image_paths: Iterable[str]) -> list[list[float]]:
    image_paths = list(image_paths)
    if not image_paths:
        return []

    try:
        import torch
        from PIL import Image
        from transformers import CLIPModel, CLIPProcessor
    except Exception:
        return [embedding_from_path(path) for path in image_paths]

    device = get_inference_device(settings)
    strict_cuda = is_strict_cuda_mode(settings)
    model_name = settings.clip_model_name
    try:
        if strict_cuda and device == "cuda":
            ensure_cuda_ready(settings)
        if device == "cuda":
            load_attempts = [
                ({"dtype": torch.float16, "low_cpu_mem_usage": False}, False),
                ({"dtype": torch.float16, "device_map": {"": device}}, True),
            ]
        else:
            load_attempts = [({"dtype": torch.float32, "low_cpu_mem_usage": False}, False)]
        model, use_device_map = load_pretrained_model(
            model_class=CLIPModel,
            model_name=model_name,
            device=device,
            load_attempts=load_attempts,
            release_memory=release_torch_memory,
            log_label=f"CLIP model {model_name}",
        )
        processor = _load_processor(CLIPProcessor, model_name)
        model.eval()
        logger.info("Running CLIP image inference with %s on %s.", model_name, device)
    except Exception:
        release_torch_memory()
        if strict_cuda and device == "cuda":
            raise
        return [embedding_from_path(path) for path in image_paths]

    embeddings: list[list[float]] = []
    try:
        with torch.inference_mode():
            for image_path in image_paths:
                image = Image.open(image_path).convert("RGB")
                inputs = processor(images=image, return_tensors="pt", input_data_format="channels_last")
                if device != "cuda" or not use_device_map:
                    inputs = inputs.to(device)
                features = model.get_image_features(**inputs)
                embeddings.append(_normalize(features).squeeze(0).cpu().tolist())
    finally:
        del model
        del processor
        release_torch_memory()

    return embeddings


def encode_text(settings, text: str) -> list[float]:
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor
    except Exception:
        return embedding_from_text(text)

    device = get_inference_device(settings)
    strict_cuda = is_strict_cuda_mode(settings)
    model_name = settings.clip_model_name
    try:
        if strict_cuda and device == "cuda":
            ensure_cuda_ready(settings)
        if device == "cuda":
            load_attempts = [
                ({"dtype": torch.float16, "low_cpu_mem_usage": False}, False),
                ({"dtype": torch.float16, "device_map": {"": device}}, True),
            ]
        else:
            load_attempts = [({"dtype": torch.float32, "low_cpu_mem_usage": False}, False)]
        model, use_device_map = load_pretrained_model(
            model_class=CLIPModel,
            model_name=model_name,
            device=device,
            load_attempts=load_attempts,
            release_memory=release_torch_memory,
            log_label=f"CLIP model {model_name}",
        )
        processor = _load_processor(CLIPProcessor, model_name)
        model.eval()
        logger.info("Running CLIP text inference with %s on %s.", model_name, device)
    except Exception:
        release_torch_memory()
        if strict_cuda and device == "cuda":
            raise
        return embedding_from_text(text)

    try:
        with torch.inference_mode():
            inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
            if device != "cuda" or not use_device_map:
                inputs = inputs.to(device)
            features = model.get_text_features(**inputs)
            return _normalize(features).squeeze(0).cpu().tolist()
    finally:
        del model
        del processor
        release_torch_memory()
