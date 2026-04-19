from __future__ import annotations

from semedia_shared.ml_inputs import build_image_inputs, move_batch_to_device


class _FakeTensor:
    def __init__(self):
        self.device: str | None = None

    def to(self, device: str):
        self.device = device
        return self


class _FakeBatch:
    def __init__(self):
        self.device: str | None = None

    def to(self, device: str):
        self.device = device
        return self


def test_build_image_inputs_uses_default_processor_layout():
    calls: list[dict] = []
    image = object()

    class _FakeProcessor:
        def __call__(self, **kwargs):
            calls.append(kwargs)
            return {"pixel_values": _FakeTensor()}

    inputs = build_image_inputs(_FakeProcessor(), image)

    assert "pixel_values" in inputs
    assert calls == [{"images": image, "return_tensors": "pt"}]


def test_move_batch_to_device_supports_mapping_inputs():
    tensor = _FakeTensor()

    moved = move_batch_to_device({"pixel_values": tensor}, "cuda")

    assert moved["pixel_values"] is tensor
    assert tensor.device == "cuda"


def test_move_batch_to_device_supports_batch_objects():
    batch = _FakeBatch()

    moved = move_batch_to_device(batch, "cuda")

    assert moved is batch
    assert batch.device == "cuda"
