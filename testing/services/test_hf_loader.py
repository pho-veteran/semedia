from __future__ import annotations

from semedia_shared.hf_loader import clear_pretrained_caches, load_cached_pretrained_model, load_pretrained_processor


class _FakeModel:
    def __init__(self):
        self.device = "cpu"

    def parameters(self):
        return []

    def buffers(self):
        return []

    def to(self, device: str):
        self.device = device
        return self


class _FakeModelClass:
    calls = 0

    @classmethod
    def from_pretrained(cls, model_name: str, **_kwargs):
        cls.calls += 1
        return _FakeModel()


class _FastProcessorClass:
    calls = 0

    @classmethod
    def from_pretrained(cls, model_name: str, use_fast: bool = False):
        cls.calls += 1
        return {"model_name": model_name, "use_fast": use_fast}


class _FallbackProcessorClass:
    calls = 0

    @classmethod
    def from_pretrained(cls, model_name: str, use_fast: bool = False):
        cls.calls += 1
        if use_fast:
            raise RuntimeError("fast unavailable")
        return {"model_name": model_name, "use_fast": use_fast}


def test_load_cached_pretrained_model_reuses_loaded_model():
    clear_pretrained_caches()
    _FakeModelClass.calls = 0

    first_model, first_use_device_map = load_cached_pretrained_model(
        model_class=_FakeModelClass,
        model_name="demo-model",
        device="cuda",
        load_attempts=[({"dtype": "float16"}, False)],
        release_memory=lambda: None,
        log_label="Demo model",
    )
    second_model, second_use_device_map = load_cached_pretrained_model(
        model_class=_FakeModelClass,
        model_name="demo-model",
        device="cuda",
        load_attempts=[({"dtype": "float16"}, False)],
        release_memory=lambda: None,
        log_label="Demo model",
    )

    assert _FakeModelClass.calls == 1
    assert first_model is second_model
    assert first_model.device == "cuda"
    assert first_use_device_map is False
    assert second_use_device_map is False


def test_load_pretrained_processor_uses_fast_processor_and_caches_result():
    clear_pretrained_caches()
    _FastProcessorClass.calls = 0

    first_processor = load_pretrained_processor(processor_class=_FastProcessorClass, model_name="processor-demo")
    second_processor = load_pretrained_processor(processor_class=_FastProcessorClass, model_name="processor-demo")

    assert _FastProcessorClass.calls == 1
    assert first_processor is second_processor
    assert first_processor["use_fast"] is True


def test_load_pretrained_processor_falls_back_once_and_caches_default_processor():
    clear_pretrained_caches()
    _FallbackProcessorClass.calls = 0

    first_processor = load_pretrained_processor(processor_class=_FallbackProcessorClass, model_name="processor-demo")
    second_processor = load_pretrained_processor(processor_class=_FallbackProcessorClass, model_name="processor-demo")

    assert _FallbackProcessorClass.calls == 2
    assert first_processor is second_processor
    assert first_processor["use_fast"] is False
