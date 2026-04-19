from __future__ import annotations


_VALID_DEVICE_REQUESTS = {"auto", "cpu", "cuda"}


def release_torch_memory() -> None:
    try:
        import torch
    except Exception:
        return

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def get_requested_device(settings) -> str:
    requested = (settings.ml_device or "auto").strip().lower()
    return requested if requested in _VALID_DEVICE_REQUESTS else "auto"


def is_strict_cuda_mode(settings) -> bool:
    return settings.ml_strict_cuda


def get_inference_device(settings) -> str:
    try:
        import torch
    except Exception:
        return "cpu"

    requested = get_requested_device(settings)
    if requested in {"auto", "cuda"}:
        return "cuda" if torch.cuda.is_available() else "cpu"
    return "cpu"


def ensure_cuda_ready(settings) -> None:
    if get_requested_device(settings) != "cuda":
        return

    try:
        import torch
    except Exception as exc:
        raise RuntimeError("CUDA was requested, but torch is not installed.") from exc

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False.")


def get_runtime_diagnostics(settings) -> dict:
    diagnostics = {
        "requested_device": get_requested_device(settings),
        "strict_cuda": is_strict_cuda_mode(settings),
        "preload_models": settings.ml_preload_models,
        "selected_device": "cpu",
        "torch_installed": False,
        "cuda_available": False,
        "cuda_device_count": 0,
        "gpu_name": "",
    }

    try:
        import torch
    except Exception:
        return diagnostics

    diagnostics["torch_installed"] = True
    diagnostics["cuda_available"] = torch.cuda.is_available()
    diagnostics["selected_device"] = get_inference_device(settings)

    if torch.cuda.is_available():
        diagnostics["cuda_device_count"] = torch.cuda.device_count()
        diagnostics["gpu_name"] = torch.cuda.get_device_name(0)

    return diagnostics
