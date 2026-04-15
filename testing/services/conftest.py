from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SEMEDIA_ROOT = Path(__file__).resolve().parents[2]
SHARED_PATH = SEMEDIA_ROOT / "services" / "shared"

if str(SHARED_PATH) not in sys.path:
    sys.path.insert(0, str(SHARED_PATH))

from semedia_shared.config import Settings
from semedia_shared.database import build_engine, build_session_factory, init_database
from semedia_shared.storage import ensure_media_root


def load_service_module(module_name: str, relative_path: str):
    module_path = SEMEDIA_ROOT / relative_path
    if module_name in sys.modules:
        del sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def make_test_settings(service_name: str, tmp_path: Path) -> Settings:
    return Settings(
        service_name=service_name,
        database_url=f"sqlite:///{(tmp_path / 'service-test.sqlite3').resolve().as_posix()}",
        media_root=tmp_path / "media",
        media_base_url="/media",
        clip_model_name="openai/clip-vit-base-patch32",
        caption_model_name="Salesforce/blip-image-captioning-base",
        scene_detection_threshold=27.0,
        search_vector_weight=0.7,
        search_keyword_weight=0.3,
        search_max_results=20,
        ml_device="cpu",
        ml_strict_cuda=False,
        media_worker_url="http://media-worker.test",
        search_api_url="http://search-api.test",
        allow_all_origins=True,
    )


@pytest.fixture
def gateway_env(tmp_path, monkeypatch):
    module = load_service_module("gateway_service_main", "services/gateway_api/app/main.py")
    settings = make_test_settings("gateway-api", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)

    monkeypatch.setattr(module, "settings", settings)
    monkeypatch.setattr(module, "engine", engine)
    monkeypatch.setattr(module, "SessionLocal", session_factory)

    ensure_media_root(settings)
    init_database(engine)

    with TestClient(module.app) as client:
        yield {
            "module": module,
            "client": client,
            "settings": settings,
            "session_factory": session_factory,
        }

    module.app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def worker_env(tmp_path, monkeypatch):
    module = load_service_module("media_worker_service_main", "services/media_worker/app/main.py")
    settings = make_test_settings("media-worker", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)

    monkeypatch.setattr(module, "settings", settings)
    monkeypatch.setattr(module, "engine", engine)
    monkeypatch.setattr(module, "SessionLocal", session_factory)

    ensure_media_root(settings)
    init_database(engine)

    with TestClient(module.app) as client:
        yield {
            "module": module,
            "client": client,
            "settings": settings,
            "session_factory": session_factory,
        }

    module.app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def search_env(tmp_path, monkeypatch):
    module = load_service_module("search_service_main", "services/search_api/app/main.py")
    settings = make_test_settings("search-api", tmp_path)
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)

    monkeypatch.setattr(module, "settings", settings)
    monkeypatch.setattr(module, "engine", engine)
    monkeypatch.setattr(module, "SessionLocal", session_factory)

    init_database(engine)

    with TestClient(module.app) as client:
        yield {
            "module": module,
            "client": client,
            "settings": settings,
            "session_factory": session_factory,
        }

    module.app.dependency_overrides.clear()
    engine.dispose()
