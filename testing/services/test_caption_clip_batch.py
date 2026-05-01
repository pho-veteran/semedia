from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

SEMEDIA_ROOT = Path(__file__).resolve().parents[2]
SHARED_PATH = SEMEDIA_ROOT / "services" / "shared"

if str(SHARED_PATH) not in sys.path:
    sys.path.insert(0, str(SHARED_PATH))

from semedia_shared.caption_service import generate_captions
from semedia_shared.clip_service import encode_images
from semedia_shared.config import Settings


@pytest.fixture
def test_settings(tmp_path):
    return Settings(
        service_name="test",
        database_url="sqlite:///:memory:",
        media_root=tmp_path / "media",
        media_base_url="/media",
        log_level="INFO",
        log_format="text",
        clip_model_name="openai/clip-vit-base-patch32",
        caption_model_name="Salesforce/blip-image-captioning-base",
        scene_detection_threshold=27.0,
        search_vector_weight=0.7,
        search_keyword_weight=0.3,
        search_max_results=20,
        ml_device="cpu",
        ml_strict_cuda=False,
        ml_preload_models=False,
        media_worker_url="http://test",
        search_api_url="http://test",
        allow_all_origins=True,
        caption_max_length=50,
        caption_min_length=10,
        caption_num_beams=5,
        caption_retry_weak=True,
        caption_retry_num_beams=8,
        caption_batch_size=8,
        caption_retry_fallback="Image content unclear.",
        caption_weak_min_words=3,
        caption_weak_min_chars=10,
        caption_retry_max_length=60,
        caption_retry_min_length=15,
    )


def test_generate_captions_batches_processor_calls(test_settings, tmp_path, monkeypatch):
    """Test that generate_captions processes images in batches, not one-by-one."""
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    batch_call_count = []

    import semedia_shared.caption_service as caption_module

    fake_torch = MagicMock()
    fake_torch.inference_mode = MagicMock()

    def fake_load_resources(settings):
        return (fake_torch, MagicMock(), settings.caption_model_name, "cpu", False, MagicMock(), MagicMock(), False)

    def fake_generate_batch(image_module, processor, model, device, use_device_map, paths, gen_kwargs):
        batch_call_count.append(len(paths))
        return [f"A descriptive caption number {i}." for i in range(len(paths))]

    monkeypatch.setattr(caption_module, "_load_caption_resources", fake_load_resources)
    monkeypatch.setattr(caption_module, "_generate_batch_captions", fake_generate_batch)
    monkeypatch.setattr(caption_module, "_is_weak_caption", lambda settings, caption: False)

    result = generate_captions(test_settings, image_paths)

    assert len(batch_call_count) == 1, f"Expected 1 batched call, got {len(batch_call_count)}"
    assert batch_call_count[0] == 3, "Expected batch to contain all 3 images"
    assert len(result) == len(image_paths), "Should return caption for each image"


def test_generate_captions_chunks_large_batches(test_settings, tmp_path, monkeypatch):
    """Test that generate_captions chunks large batches to prevent memory issues."""
    image_paths = []
    for i in range(20):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    batch_sizes = []

    import semedia_shared.caption_service as caption_module

    fake_torch = MagicMock()

    def fake_load_resources(settings):
        return (fake_torch, MagicMock(), settings.caption_model_name, "cpu", False, MagicMock(), MagicMock(), False)

    def fake_generate_batch(torch, processor, model, device, use_device_map, paths, gen_kwargs):
        batch_sizes.append(len(paths))
        return [f"A descriptive caption {i}." for i in range(len(paths))]

    monkeypatch.setattr(caption_module, "_load_caption_resources", fake_load_resources)
    monkeypatch.setattr(caption_module, "_generate_batch_captions", fake_generate_batch)
    monkeypatch.setattr(caption_module, "_is_weak_caption", lambda settings, caption: False)

    result = generate_captions(test_settings, image_paths)

    assert batch_sizes == [8, 8, 4], f"Expected chunk sizes [8, 8, 4], got {batch_sizes}"
    assert len(result) == len(image_paths), "Should return caption for each image"


def test_generate_captions_preserves_order(test_settings, tmp_path, monkeypatch):
    """Test that generate_captions returns captions in the same order as input paths."""
    image_paths = []
    for i in range(5):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.caption_service as caption_module

    fake_torch = MagicMock()

    def fake_load_resources(settings):
        return (fake_torch, MagicMock(), settings.caption_model_name, "cpu", False, MagicMock(), MagicMock(), False)

    call_index = {"value": 0}

    def fake_generate_batch(image_module, processor, model, device, use_device_map, paths, gen_kwargs):
        start = call_index["value"]
        call_index["value"] += len(paths)
        return [f"Caption number {start + i} is here." for i in range(len(paths))]

    monkeypatch.setattr(caption_module, "_load_caption_resources", fake_load_resources)
    monkeypatch.setattr(caption_module, "_generate_batch_captions", fake_generate_batch)
    monkeypatch.setattr(caption_module, "_is_weak_caption", lambda settings, caption: False)

    result = generate_captions(test_settings, image_paths)

    assert result == [
        "Caption number 0 is here.",
        "Caption number 1 is here.",
        "Caption number 2 is here.",
        "Caption number 3 is here.",
        "Caption number 4 is here.",
    ]


def test_encode_images_batches_model_calls(test_settings, tmp_path, monkeypatch):
    """Test that encode_images processes images in batches, not one-by-one."""
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    processor_calls = []
    feature_calls = []

    class FakeProcessor:
        def __call__(self, **kwargs):
            processor_calls.append(kwargs)
            return {"pixel_values": MagicMock()}

    class FakeFeatures:
        def norm(self, p, dim, keepdim):
            return MagicMock(return_value=MagicMock())

        def __truediv__(self, other):
            result = MagicMock()
            result.cpu.return_value.tolist.return_value = [[0.1, 0.2, 0.3] for _ in range(3)]
            return result

    class FakeModel:
        def eval(self):
            return self

        def get_image_features(self, **kwargs):
            feature_calls.append(kwargs)
            return FakeFeatures()

    import semedia_shared.clip_service as clip_module

    fake_torch = MagicMock()
    fake_Image = MagicMock()
    fake_processor = FakeProcessor()
    fake_model = FakeModel()

    def fake_load_resources(settings):
        return (fake_torch, fake_Image, settings.clip_model_name, "cpu", False, fake_processor, fake_model, False)

    monkeypatch.setattr(clip_module, "_load_clip_resources", fake_load_resources)

    def fake_build_image_inputs(processor, images):
        return processor(images=images, return_tensors="pt")

    monkeypatch.setattr(clip_module, "build_image_inputs", fake_build_image_inputs)

    result = encode_images(test_settings, image_paths)

    # Verify batched processing
    assert len(feature_calls) < len(image_paths), "Expected batched feature calls, got per-image calls"
    assert len(result) == len(image_paths), "Should return embedding for each image"


def test_encode_images_chunks_large_batches(test_settings, tmp_path, monkeypatch):
    """Test that encode_images chunks large batches to prevent memory issues."""
    image_paths = []
    for i in range(20):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    batch_sizes = []

    class FakeProcessor:
        def __call__(self, **kwargs):
            images = kwargs.get("images", [])
            batch_size = len(images) if isinstance(images, list) else 1
            batch_sizes.append(batch_size)
            return {"pixel_values": MagicMock()}

    class FakeFeatures:
        def __init__(self, batch_size):
            self.batch_size = batch_size

        def cpu(self):
            return self

        def tolist(self):
            return [[0.1, 0.2] for _ in range(self.batch_size)]

    class FakeModel:
        def eval(self):
            return self

        def get_image_features(self, **kwargs):
            current_batch_size = batch_sizes[-1]
            return FakeFeatures(current_batch_size)

    import semedia_shared.clip_service as clip_module

    fake_torch = MagicMock()
    fake_Image = MagicMock()
    fake_processor = FakeProcessor()
    fake_model = FakeModel()

    def fake_load_resources(settings):
        return (fake_torch, fake_Image, settings.clip_model_name, "cpu", False, fake_processor, fake_model, False)

    monkeypatch.setattr(clip_module, "_load_clip_resources", fake_load_resources)

    def fake_normalize(features):
        return features

    monkeypatch.setattr(clip_module, "_normalize", fake_normalize)

    result = encode_images(test_settings, image_paths)

    assert batch_sizes == [8, 8, 4], f"Expected chunk sizes [8, 8, 4], got {batch_sizes}"
    assert len(result) == len(image_paths), "Should return embedding for each image"


def test_encode_images_preserves_order(test_settings, tmp_path, monkeypatch):
    """Test that encode_images returns embeddings in the same order as input paths."""
    image_paths = []
    for i in range(5):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    class FakeProcessor:
        def __call__(self, **kwargs):
            return {"pixel_values": MagicMock()}

    class FakeFeatures:
        def __init__(self, batch_size):
            self.batch_size = batch_size

        def cpu(self):
            return self

        def tolist(self):
            return [[float(i), float(i) * 2] for i in range(self.batch_size)]

    class FakeModel:
        def eval(self):
            return self

        def get_image_features(self, **kwargs):
            return FakeFeatures(5)

    import semedia_shared.clip_service as clip_module

    fake_torch = MagicMock()
    fake_Image = MagicMock()
    fake_processor = FakeProcessor()
    fake_model = FakeModel()

    def fake_load_resources(settings):
        return (fake_torch, fake_Image, settings.clip_model_name, "cpu", False, fake_processor, fake_model, False)

    monkeypatch.setattr(clip_module, "_load_clip_resources", fake_load_resources)

    def fake_normalize(features):
        return features

    monkeypatch.setattr(clip_module, "_normalize", fake_normalize)

    result = encode_images(test_settings, image_paths)

    expected = [[0.0, 0.0], [1.0, 2.0], [2.0, 4.0], [3.0, 6.0], [4.0, 8.0]]
    assert result == expected, f"Expected {expected}, got {result}"


def test_generate_captions_falls_back_when_inference_fails(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(2):
        img_path = tmp_path / f"fallback_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.caption_service as caption_module

    fake_torch = MagicMock()

    def fake_load_resources(settings):
        return (fake_torch, MagicMock(), settings.caption_model_name, "cpu", False, MagicMock(), MagicMock(), False)

    def fake_generate_batch(torch, processor, model, device, use_device_map, paths, gen_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(caption_module, "_load_caption_resources", fake_load_resources)
    monkeypatch.setattr(caption_module, "_generate_batch_captions", fake_generate_batch)
    monkeypatch.setattr(caption_module, "_is_weak_caption", lambda settings, caption: False)

    fallback_calls = []

    def fake_fallback_captions(paths):
        fallback_calls.extend(paths)
        return [f"Fallback: {Path(path).name}" for path in paths]

    monkeypatch.setattr(caption_module, "_fallback_captions", fake_fallback_captions)

    result = generate_captions(test_settings, image_paths)

    assert fallback_calls == image_paths
    assert result == [f"Fallback: {Path(path).name}" for path in image_paths]


def test_encode_images_falls_back_when_inference_fails(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(2):
        img_path = tmp_path / f"fallback_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.clip_service as clip_module

    fake_torch = MagicMock()
    fake_Image = MagicMock()
    fake_processor = MagicMock()

    class FakeModel:
        def eval(self):
            return self

        def get_image_features(self, **kwargs):
            raise RuntimeError("boom")

    def fake_load_resources(settings):
        return (fake_torch, fake_Image, settings.clip_model_name, "cpu", False, fake_processor, FakeModel(), False)

    monkeypatch.setattr(clip_module, "_load_clip_resources", fake_load_resources)

    fallback_calls = []

    def fake_embedding_from_path(path):
        fallback_calls.append(path)
        return [float(len(fallback_calls)), 0.0]

    monkeypatch.setattr(clip_module, "embedding_from_path", fake_embedding_from_path)

    result = encode_images(test_settings, image_paths)

    assert fallback_calls == image_paths
    assert result == [[1.0, 0.0], [2.0, 0.0]]


def test_generate_captions_uses_build_image_inputs_for_batches(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.caption_service as caption_module

    fake_torch = MagicMock()
    fake_image_module = MagicMock()
    fake_image_module.open.side_effect = lambda path: MagicMock(convert=lambda mode: f"image:{Path(path).name}")

    class FakeProcessor:
        def batch_decode(self, output_ids, skip_special_tokens=True):
            return ["A descriptive caption."] * len(output_ids)

    class FakeModel:
        def eval(self):
            return self

        def generate(self, **kwargs):
            return [MagicMock() for _ in range(3)]

    def fake_load_resources(settings):
        return (fake_torch, fake_image_module, settings.caption_model_name, "cpu", False, FakeProcessor(), FakeModel(), False)

    monkeypatch.setattr(caption_module, "_load_caption_resources", fake_load_resources)

    build_calls = []

    def fake_build_image_inputs(processor, images):
        build_calls.append(images)
        return {"pixel_values": MagicMock()}

    monkeypatch.setattr(caption_module, "build_image_inputs", fake_build_image_inputs)

    generate_captions(test_settings, image_paths)

    assert len(build_calls) == 1
    assert isinstance(build_calls[0], list)
    assert len(build_calls[0]) == 3


def test_encode_images_uses_build_image_inputs_for_batches(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.clip_service as clip_module

    fake_torch = MagicMock()
    fake_Image = MagicMock()

    class FakeModel:
        def eval(self):
            return self

        def get_image_features(self, **kwargs):
            features = MagicMock()
            features.cpu.return_value.tolist.return_value = [[0.1, 0.2] for _ in range(3)]
            return features

    def fake_load_resources(settings):
        return (fake_torch, fake_Image, settings.clip_model_name, "cpu", False, MagicMock(), FakeModel(), False)

    monkeypatch.setattr(clip_module, "_load_clip_resources", fake_load_resources)
    monkeypatch.setattr(clip_module, "_normalize", lambda features: features)

    build_calls = []

    def fake_build_image_inputs(processor, images):
        build_calls.append(images)
        return {"pixel_values": MagicMock()}

    monkeypatch.setattr(clip_module, "build_image_inputs", fake_build_image_inputs)

    encode_images(test_settings, image_paths)

    assert len(build_calls) == 1
    assert isinstance(build_calls[0], list)
    assert len(build_calls[0]) == 3


def test_generate_captions_load_failure_uses_fallback(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(2):
        img_path = tmp_path / f"load_fail_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.caption_service as caption_module

    def fake_load_resources(settings):
        raise RuntimeError("load failed")

    monkeypatch.setattr(caption_module, "_load_caption_resources", fake_load_resources)
    monkeypatch.setattr(caption_module, "_fallback_captions", lambda paths: [f"Fallback: {Path(path).name}" for path in paths])

    assert generate_captions(test_settings, image_paths) == [
        "Fallback: load_fail_0.jpg",
        "Fallback: load_fail_1.jpg",
    ]


def test_encode_images_load_failure_uses_fallback(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(2):
        img_path = tmp_path / f"load_fail_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.clip_service as clip_module

    def fake_load_resources(settings):
        raise RuntimeError("load failed")

    monkeypatch.setattr(clip_module, "_load_clip_resources", fake_load_resources)
    monkeypatch.setattr(clip_module, "embedding_from_path", lambda path: [float(Path(path).stem.split('_')[-1]), 1.0])

    assert encode_images(test_settings, image_paths) == [[0.0, 1.0], [1.0, 1.0]]


def test_generate_captions_maintains_order_across_chunks(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(10):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.caption_service as caption_module

    fake_torch = MagicMock()
    batch_sizes = []
    next_index = {"value": 0}

    monkeypatch.setattr(
        caption_module,
        "_load_caption_resources",
        lambda settings: (fake_torch, MagicMock(), settings.caption_model_name, "cpu", False, MagicMock(), MagicMock(), False),
    )

    def fake_generate_batch(image_module, processor, model, device, use_device_map, paths, gen_kwargs):
        batch_sizes.append(len(paths))
        start = next_index["value"]
        next_index["value"] += len(paths)
        return [f"Caption number {start + i} is here." for i in range(len(paths))]

    monkeypatch.setattr(caption_module, "_generate_batch_captions", fake_generate_batch)
    monkeypatch.setattr(caption_module, "_is_weak_caption", lambda settings, caption: False)

    result = generate_captions(test_settings, image_paths)

    assert batch_sizes == [8, 2]
    assert result == [f"Caption number {i} is here." for i in range(10)]


def test_encode_images_maintains_order_across_chunks(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(10):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.clip_service as clip_module

    fake_torch = MagicMock()
    fake_Image = MagicMock()
    batch_sizes = []
    chunk_index = {"value": 0}

    class FakeProcessor:
        def __call__(self, **kwargs):
            images = kwargs.get("images", [])
            batch_sizes.append(len(images))
            return {"pixel_values": MagicMock()}

    class FakeFeatures:
        def __init__(self, values):
            self.values = values

        def cpu(self):
            return self

        def tolist(self):
            return self.values

    class FakeModel:
        def eval(self):
            return self

        def get_image_features(self, **kwargs):
            start = 0 if chunk_index["value"] == 0 else 8
            size = batch_sizes[-1]
            chunk_index["value"] += 1
            return FakeFeatures([[float(start + i), float(start + i) * 2] for i in range(size)])

    monkeypatch.setattr(clip_module, "_load_clip_resources", lambda settings: (fake_torch, fake_Image, settings.clip_model_name, "cpu", False, FakeProcessor(), FakeModel(), False))
    monkeypatch.setattr(clip_module, "_normalize", lambda features: features)

    result = encode_images(test_settings, image_paths)

    assert batch_sizes == [8, 2]
    assert result == [[float(i), float(i) * 2] for i in range(10)]


def test_move_batch_to_device_is_used_for_caption_batches(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.caption_service as caption_module

    fake_torch = MagicMock()
    fake_image_module = MagicMock()
    fake_image_module.open.side_effect = lambda path: MagicMock(convert=lambda mode: f"image:{Path(path).name}")

    class FakeProcessor:
        def batch_decode(self, output_ids, skip_special_tokens=True):
            return ["A descriptive caption."] * len(output_ids)

    class FakeModel:
        def eval(self):
            return self

        def generate(self, **kwargs):
            return [MagicMock() for _ in range(3)]

    monkeypatch.setattr(caption_module, "_load_caption_resources", lambda settings: (fake_torch, fake_image_module, settings.caption_model_name, "cpu", False, FakeProcessor(), FakeModel(), False))
    monkeypatch.setattr(caption_module, "build_image_inputs", lambda processor, images: {"pixel_values": MagicMock()})

    move_calls = []

    def fake_move_batch_to_device(inputs, device):
        move_calls.append(device)
        return inputs

    monkeypatch.setattr(caption_module, "move_batch_to_device", fake_move_batch_to_device)

    generate_captions(test_settings, image_paths)

    assert move_calls == ["cpu"]


def test_move_batch_to_device_is_used_for_clip_batches(test_settings, tmp_path, monkeypatch):
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"image_{i}.jpg"
        img_path.write_bytes(b"fake image data")
        image_paths.append(str(img_path))

    import semedia_shared.clip_service as clip_module

    fake_torch = MagicMock()
    fake_Image = MagicMock()

    class FakeModel:
        def eval(self):
            return self

        def get_image_features(self, **kwargs):
            features = MagicMock()
            features.cpu.return_value.tolist.return_value = [[0.1, 0.2] for _ in range(3)]
            return features

    monkeypatch.setattr(clip_module, "_load_clip_resources", lambda settings: (fake_torch, fake_Image, settings.clip_model_name, "cpu", False, MagicMock(), FakeModel(), False))
    monkeypatch.setattr(clip_module, "build_image_inputs", lambda processor, images: {"pixel_values": MagicMock()})
    monkeypatch.setattr(clip_module, "_normalize", lambda features: features)

    move_calls = []

    def fake_move_batch_to_device(inputs, device):
        move_calls.append(device)
        return inputs

    monkeypatch.setattr(clip_module, "move_batch_to_device", fake_move_batch_to_device)

    encode_images(test_settings, image_paths)

    assert move_calls == ["cpu"]

