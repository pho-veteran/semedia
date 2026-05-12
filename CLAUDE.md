# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is the Semedia semantic media search application. All implementation work happens in `Semedia/`.

```
Semedia/
  services/
    gateway_api/   # Public-facing API: upload, media CRUD, runtime, search proxy
    media_worker/  # GPU-bound processing: scene detection, captioning, CLIP embeddings
    search_api/    # Hybrid retrieval: vector + keyword search, ranking
    shared/        # Shared models, database, storage, pipeline, and search logic
  frontend/        # React + TypeScript UI with Vite
  testing/         # Service tests (pytest), evaluation framework, and smoke tests
  docs/            # Architecture, plans, metrics, and implementation tracking
```

Active backend services are FastAPI apps with entrypoints at `services/{service_name}/app/main.py`. The `shared/` package (`semedia_shared`) contains SQLAlchemy models (`MediaItem`, `VideoScene`), processing pipeline logic, and search helpers used across all services.

**Project documentation structure:**
- `docs/plan.md` — search quality improvement roadmap (Phases 1–11)
- `docs/TASKS.md` — implementation task tracking and progress summary
- `docs/metrics/search_quality_history.md` — baseline and tuning history
- `docs/metrics/search_tuning_checklist.md` — parameter tuning workflow
- `docs/implementations/` — phase-specific implementation notes
- `docs/superpowers/specs/` and `docs/superpowers/plans/` — design specs and implementation plans

## Architecture

**Service interaction flow:**
1. `gateway-api` receives uploads, stores files, creates `MediaItem` records, and triggers processing through `media-worker`
2. `media-worker` runs the processing pipeline: adaptive scene detection, caption generation, and CLIP embeddings
3. `search-api` loads the durable keyword index at startup and performs hybrid retrieval plus reranking/diversity
4. `gateway-api` proxies search requests to `search-api` and serves media files back to the frontend
5. `frontend` consumes normalized search scores, explanation fields, grouped video-scene results, and metadata-based sorting fields

**Current search stack:**
- Vector retrieval: local cosine similarity over CLIP embeddings
- Keyword retrieval: durable TF-IDF artifacts rebuilt when the library changes
- Ranking: weighted fusion, reranking boosts, score normalization, and diversity limits
- Evaluation: locked local benchmark corpus, judged query set, offline baseline reports, and tuning checklist

**Data model:**
- `MediaItem`: original file, media type, processing status, duration, caption, embedding, upload metadata, and search-facing fields
- `VideoScene`: parent media, scene index, timestamps, keyframe/thumbnail paths, caption, embedding, and scene-level search data
- `KeywordIndexArtifact`: persisted keyword index payloads and version metadata
- Images are indexed directly from `MediaItem`; videos are indexed through `VideoScene`

**Key shared modules** (`Semedia/services/shared/semedia_shared/`):
- `models.py` — SQLAlchemy models (`MediaItem`, `VideoScene`, `KeywordIndexArtifact`, `ProcessingStatus`)
- `pipeline.py` — `process_media()` orchestration and index rebuild hooks
- `search_service.py` — text/image search entrypoints and candidate generation
- `ranking_service.py` — fusion, reranking, diversity, and normalized score handling
- `index_service.py` — durable TF-IDF build/load/search helpers
- `caption_service.py` — caption generation and cleanup flow
- `clip_service.py` — CLIP text and image embedding
- `video_service.py` — scene extraction, adaptive thresholds, and keyframe generation
- `serialization.py` — API response shaping, including score/explanation fields
- `config.py` — settings for ML, search weights, diversity caps, and batching
- `storage.py`, `database.py`, `log.py`, `runtime.py`, `model_warmup.py`, `hf_loader.py`, `ml_inputs.py`, `media_types.py` — shared infrastructure and model/runtime helpers

**Current roadmap context:**
- Phases 1–7 of the search quality plan are complete
- The current next engineering target is Phase 8: expand candidate generation before further tuning work
- Use `docs/plan.md`, `docs/TASKS.md`, and `docs/metrics/` as the source of truth for search-quality progress rather than older assumptions in past notes

**Project scope rule:** Keep all project-specific plans, implementation notes, and working documents inside `Semedia/docs/`. Prefer `docs/implementations/` for implementation notes and `docs/metrics/` for evaluation/tuning records.

## Commands

### Docker Compose (from `Semedia/`)

Start the full stack:
```bash
docker compose up -d --build gateway-api frontend
```

Check service health:
```bash
docker compose ps
curl http://127.0.0.1:8000/api/v1/health/
```

Stop the stack:
```bash
docker compose down
```

The default `media-worker` service installs CUDA-capable PyTorch, preloads caption and CLIP models during startup, and runs in strict CUDA mode (`ML_STRICT_CUDA=1`). It requires GPU access via `gpus: all` in `docker-compose.yml`.

### Backend Testing (from `Semedia/`)

Run all service tests:
```bash
docker compose --profile test run --rm --build service-tests
```

Run a specific test file:
```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py -v
```

Run a specific test:
```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py::test_upload_image -v
```

Backend tests use pytest with fixtures defined in `testing/services/conftest.py`. Each fixture (`gateway_env`, `worker_env`, `search_env`) provides an isolated SQLite database, temporary media storage, and a FastAPI `TestClient`. Tests run with `ML_DEVICE=cpu` and `ML_PRELOAD_MODELS=False` to avoid GPU dependencies.

### Evaluation Framework (from `Semedia/`)

Seed the locked benchmark corpus:
```bash
docker compose --profile test run --rm service-tests python testing/evaluation/seed_media.py
```

Run evaluation against the current stack:
```bash
docker compose --profile test run --rm service-tests \
  python testing/evaluation/run_evaluation.py \
  --base-url http://gateway-api:8000 \
  --queries testing/evaluation/queries.json \
  --output testing/evaluation/baselines/report-YYYY-MM-DD.json
```

Run evaluation with baseline comparison:
```bash
docker compose --profile test run --rm service-tests \
  python testing/evaluation/run_evaluation.py \
  --base-url http://gateway-api:8000 \
  --queries testing/evaluation/queries.json \
  --output testing/evaluation/baselines/report-YYYY-MM-DD.json \
  --compare-to testing/evaluation/baselines/baseline-phase7.json
```

The evaluation framework uses a locked local corpus (`testing/evaluation/assets/`), a 120-query judged benchmark (`testing/evaluation/queries.json`), and saved baseline reports for regression detection. See `docs/metrics/search_tuning_checklist.md` for the full tuning workflow.

### Smoke Testing (from `Semedia/`)

Run the end-to-end smoke test through Docker (requires stack running):
```bash
docker compose --profile test run --rm service-tests python testing/smoke_stack.py
```

This validates frontend reachability, gateway health/runtime, image upload, video upload, search, and delete using assets in `testing/smoke-assets/`.

### Frontend

Default frontend execution should go through Docker with the rest of the stack:
```bash
docker compose up -d --build frontend
```

If the user explicitly asks for local frontend-only work, the app also supports the standard Vite workflow from `Semedia/frontend/`:
```bash
npm install
npm run dev
npm run build
npm run lint
npm test
```

Frontend is configured for Vitest with jsdom (see `vite.config.ts`), but coverage is still minimal. The frontend targets `http://127.0.0.1:8000` (configured via `VITE_API_BASE_URL`).
If frontend behavior changes, prefer validating it against the Dockerized stack.

## Configuration

Key backend environment variables (see `docker-compose.yml` and `services/shared/semedia_shared/config.py` for defaults):
- `DATABASE_URL`: PostgreSQL connection string (SQLite in tests)
- `MEDIA_ROOT`, `MEDIA_BASE_URL`: File storage paths
- `ML_DEVICE`: `auto`, `cuda`, or `cpu`
- `ML_STRICT_CUDA`: `1` fails fast if CUDA is unavailable when expected
- `ML_PRELOAD_MODELS`: `1` preloads caption and CLIP models during startup
- `CLIP_MODEL_NAME`: Default `openai/clip-vit-base-patch16`
- `CAPTION_MODEL_NAME`: Default `Salesforce/blip-image-captioning-large`
- `SCENE_DETECTION_THRESHOLD`: Base threshold default `27.0`
- `SEARCH_VECTOR_WEIGHT`, `SEARCH_KEYWORD_WEIGHT`: Hybrid fusion weights (default `0.7` / `0.3`)
- `SEARCH_MAX_RESULTS`: Maximum results returned to the client
- `SEARCH_MAX_PER_MEDIA`: Diversity cap for scenes from the same media item
- `CAPTION_MAX_LENGTH`, `CAPTION_MIN_LENGTH`, `CAPTION_NUM_BEAMS`, `CAPTION_RETRY_WEAK`, `CAPTION_RETRY_NUM_BEAMS`, `CAPTION_BATCH_SIZE`: Caption quality and throughput settings
- `MEDIA_WORKER_URL`: Worker service URL for gateway and search-api
- `SEARCH_API_URL`: Search service URL for gateway
- `CORS_ALLOW_ALL_ORIGINS`: Enable permissive CORS for local development (default `1`)
- `LOG_LEVEL`, `LOG_FORMAT`: Logging configuration

Frontend configuration is in `frontend/.env` (copy from `.env.example`).

## Development Notes

**Current system state:**
- Phase 7 evaluation framework is complete
- The locked benchmark, saved baseline, metrics history, and tuning checklist are all in-project
- The next planned work is broader candidate generation (Phase 8)

**Locked architecture decisions:**
- Backend: FastAPI
- Database: PostgreSQL (SQLite in tests only)
- Video segmentation: PySceneDetect with adaptive thresholds
- Captioning: Hugging Face BLIP image captioning pipeline
- Embeddings: CLIP `openai/clip-vit-base-patch16`
- Vector retrieval: local cosine search (no external vector DB yet)
- Keyword retrieval: durable TF-IDF artifacts persisted in the app
- Ranking semantics: normalized backend scores in `[0, 1]`, surfaced to the frontend with explanation metadata

**Workflow rules for this repo:**
- Prefer Docker-based execution for stack operations, backend tests, and evaluation work
- Use `ccc` for semantic code search and index-backed exploration before falling back to manual greps
- For long coding tasks, split independent work across multiple Sonnet subagents and monitor their progress
- Keep search-quality tracking updated when work changes the evaluation baseline or tuning state
- If search behavior changes materially, rerun the relevant evaluation commands and update `docs/metrics/search_quality_history.md`
- Use `testing/evaluation/baselines/baseline-phase7.json` as the current accepted baseline unless the user asks to replace it

**Code style:**
- Python: 4-space indentation, snake_case for functions/variables
- Frontend: 2-space indentation, PascalCase for components, camelCase for hooks/utilities
- Follow the existing feature-oriented frontend structure (pages, components, api, utils, types)

**Testing strategy:**
- Backend: pytest with isolated fixtures per service, SQLite for tests, CPU-only ML in tests
- Evaluation: Docker-run offline benchmark against the locked corpus and judged query set
- Frontend: Vitest + Testing Library configured, but coverage is still minimal
- Smoke tests: end-to-end validation with real assets in `testing/smoke_stack.py`

**Security and hygiene:**
- Do not commit secrets, model weights, build artifacts, or uploaded media outside the intentional locked evaluation corpus
- Do not add ad hoc temp files under `testing/evaluation/assets/`; keep that corpus locked and intentional
- Use `.env` files for configuration and keep Docker-only/test artifacts cleaned up after one-off runs when possible
- Avoid creating new repo-level planning documents outside `Semedia/docs/`.
