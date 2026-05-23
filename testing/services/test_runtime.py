from __future__ import annotations

import sys
from dataclasses import replace
from types import SimpleNamespace

from semedia_shared.runtime import get_inference_device, get_requested_device, get_runtime_diagnostics

from .conftest import make_test_settings


class _FakeCuda:
    def __init__(self, available: bool):
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def device_count(self) -> int:
        return 1 if self._available else 0

    def get_device_name(self, _index: int) -> str:
        return "Test GPU"


def _fake_torch(available: bool):
    return SimpleNamespace(cuda=_FakeCuda(available))


def test_auto_device_prefers_cuda_when_available(tmp_path, monkeypatch):
    settings = replace(make_test_settings("media-worker", tmp_path), ml_device="auto")
    monkeypatch.setitem(sys.modules, "torch", _fake_torch(True))

    diagnostics = get_runtime_diagnostics(settings)

    assert get_requested_device(settings) == "auto"
    assert get_inference_device(settings) == "cuda"
    assert diagnostics["selected_device"] == "cuda"
    assert diagnostics["cuda_available"] is True
    assert diagnostics["gpu_name"] == "Test GPU"


def test_auto_device_falls_back_to_cpu_when_cuda_is_unavailable(tmp_path, monkeypatch):
    settings = replace(make_test_settings("media-worker", tmp_path), ml_device="auto")
    monkeypatch.setitem(sys.modules, "torch", _fake_torch(False))

    diagnostics = get_runtime_diagnostics(settings)

    assert get_requested_device(settings) == "auto"
    assert get_inference_device(settings) == "cpu"
    assert diagnostics["selected_device"] == "cpu"
    assert diagnostics["cuda_available"] is False
    assert diagnostics["gpu_name"] == ""
