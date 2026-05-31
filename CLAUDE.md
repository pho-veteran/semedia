# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is the Semedia semantic media search application. All implementation work happens in `Semedia/`.

```
Semedia/
  services/
    gateway_api/   # Public-facing API: upload, media CRUD, runtime, search proxy
    media_worker/  # GPU-bound processing: scene detection, captioning, CLIP embeddings, text/image embed endpoints, cross-encoder rerank
    search_api/    # Hybrid retrieval: vector + keyword search, ranking, optional cross-encoder rerank via media-worker
    shared/        # Shared models, database, storage, pipeline, search logic, config, rerank, serialization
  frontend/        # React 19 + TypeScript UI with Vite 8, Tailwind CSS, Radix UI primitives
  testing/         # Service tests (pytest), evaluation framework, smoke tests, benchmark validation
  docs/            # Architecture, plans, metrics, implementation tracking, college reports
```

Active backend services are FastAPI apps with entrypoints at `services/{service_name}/app/main.py`. The `shared/` package (`semedia_shared`) contains SQLAlchemy models (`MediaItem`, `VideoScene`), processing pipeline logic, and search helpers used across all services.

**Current phase:** Phase 12 complete (2026-05-30) — accuracy audit remediation. Baseline `phase12-e5-c1` in `docs/metrics/search_quality_history.md`. Only B4 (BM25 keyword enrichment) deferred.

**Project documentation structure:**
- `docs/plan.md` — search quality improvement roadmap (Phases 1–11)
- `docs/TASKS.md` — implementation task tracking and progress summary (Phase 12)
- `docs/metrics/search_quality_history.md` — baseline and tuning history (current: phase12-e5-c1)
- `docs/metrics/evaluation_benchmark_rubric.md` — metric-interpretation caveats (P@10 cap; prefer Recall/MRR/NDCG)
- `docs/metrics/search_tuning_checklist.md` — parameter tuning workflow
- `docs/implementations/` — phase-specific implementation notes (including accuracy-audit-2026-05-29.md)
- `docs/superpowers/specs/` and `docs/superpowers/plans/` — design specs and implementation plans
- `docs/college-reports/` — college project reports

## Architecture

**Service interaction flow:**
1. `gateway-api` receives uploads, stores files, creates `MediaItem` records, and triggers processing through `media-worker`
2. `media-worker` runs the processing pipeline: adaptive scene detection, caption generation, CLIP embeddings, text/image embed endpoints, and cross-encoder rerank
3. `search-api` loads the durable keyword index at startup and performs hybrid retrieval plus reranking/diversity. For text search, calls media-worker for text embedding; for image search, calls media-worker for image embedding. Optional cross-encoder rerank proxies through media-worker's `/internal/rerank` endpoint.
4. `gateway-api` proxies search requests to `search-api` and serves media files back to the frontend
5. `frontend` consumes normalized search scores, explanation fields, grouped video-scene results, and metadata-based sorting fields

**Current search stack:**
- Vector retrieval: local cosine similarity over CLIP embeddings with calibrated scaling (affine band 0.15–0.40)
- Keyword retrieval: durable TF-IDF artifacts rebuilt when the library changes
- CLIP query prompt templating/ensembling for text queries (B2)
- Multi-frame scene representation: sample N=3 frames, mean-pool embeddings (B3)
- Ranking: weighted fusion (0.7 vector / 0.3 keyword), Reciprocal Rank Fusion calibration, reranking boosts, diversity limits, optional cross-encoder rerank (default-OFF, gated by `SEARCH_RERANK_ENABLED` — measured to regress on this corpus with MS-MARCO passage reranker)
- Configurable relevance score floor (`SEARCH_MIN_SCORE`, default 0.0) applied after diversity
- Evaluation: 120-query judged benchmark, 35-asset locked corpus, video-granularity scene credit (E5), by-image search evaluation

**Data model:**
- `MediaItem`: original file, media type, processing status, duration, caption, embedding, upload metadata, and search-facing fields
- `VideoScene`: parent media, scene index, timestamps, keyframe/thumbnail paths, caption, embedding, and scene-level search data
- `KeywordIndexArtifact`: persisted keyword index payloads and version metadata
- Images are indexed directly from `MediaItem`; videos are indexed through `VideoScene`

**Key shared modules** (`services/shared/semedia_shared/`):
- `models.py` — SQLAlchemy models (`MediaItem`, `VideoScene`, `KeywordIndexArtifact`, `ProcessingStatus`)
- `pipeline.py` — `process_media()` orchestration, multi-frame scene embedding, and index rebuild hooks
- `search_service.py` — text/image search entrypoints, candidate generation, CLIP similarity calibration, relevance floor
- `ranking_service.py` — fusion, reranking (heuristic + optional cross-encoder), diversity, score calibration, result explanation
- `index_service.py` — durable TF-IDF build/load/search helpers
- `caption_service.py` — caption generation, cleanup flow, weak-caption filtering
- `caption_cleanup_config.py` — caption cleanup configuration and normalization patterns
- `clip_service.py` — CLIP text (with prompt templating/ensembling) and image embedding, batched inference
- `video_service.py` — scene extraction, adaptive thresholds, multi-frame keyframe generation
- `rerank_service.py` — cross-encoder rerank model loading and scoring (MS-MARCO MiniLM)
- `serialization.py` — API response shaping (scene payload, media summary, media detail)
- `config.py` — settings dataclass with all ML, search, caption, and runtime config
- `storage.py`, `database.py`, `log.py`, `runtime.py`, `model_warmup.py`, `hf_loader.py`, `ml_inputs.py`, `media_types.py`, `migrations.py`, `reprocess.py`, `fallback_ai.py` — shared infrastructure

**Current roadmap context:**
- Phases 1–7 complete (processing, keyword index, caption quality, ranking/diversity, UI presentation, evaluation framework)
- Phase 12 complete (accuracy audit remediation) — E5 video-level scene credit gives R@10 0.98 / MRR 0.87
- E5 + C1 done (C1 measured to regress, kept default-off)
- Only B4 (BM25 keyword enrichment) deferred
- Use `docs/plan.md`, `docs/TASKS.md`, and `docs/metrics/` as the source of truth for search-quality progress

**Project scope rule:** Keep all project-specific plans, implementation notes, and working documents inside `docs/`. Prefer `docs/implementations/` for implementation notes and `docs/metrics/` for evaluation/tuning records.

## Commands

### Docker Compose (from repo root)

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

The default `media-worker` service installs CUDA-capable PyTorch, preloads caption, CLIP, and rerank models during startup, and runs in strict CUDA mode (`ML_STRICT_CUDA=1`). It requires GPU access via `gpus: all` in `docker-compose.yml`.

### Backend Testing (from repo root)

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

Backend tests use pytest with fixtures defined in `testing/services/conftest.py`. Each fixture (`gateway_env`, `worker_env`, `search_env`) provides an isolated SQLite database, temporary media storage, and a FastAPI `TestClient`. Tests run with `ML_DEVICE=cpu` and `ML_PRELOAD_MODELS=False` to avoid GPU dependencies. Test settings use lighter models (`clip-vit-base-patch32`, `blip-image-captioning-base`).

**Test files available:**
- `test_gateway_api.py` — upload, list, detail, delete, health, runtime, search proxy
- `test_media_worker_api.py` — health, runtime, embed text/image, process, rerank
- `test_media_worker_pipeline.py` — image/video processing pipeline end-to-end
- `test_search_api.py` — text search, image search, health, error handling
- `test_ranking_service.py` — fusion, reranking, diversity, score calibration, explanation
- `test_caption_service.py` — caption generation, weak filtering, cleanup
- `test_caption_clip_batch.py` — batched caption and CLIP inference
- `test_clip_prompts.py` — CLIP text prompt templating/ensembling
- `test_hf_loader.py`, `test_logging.py`, `test_ml_inputs.py`, `test_reprocess.py`, `test_runtime.py`, `test_search_metadata.py`

### Evaluation Framework (from repo root)

**Validation** — validate benchmark artifacts and query judgments:
```bash
docker compose --profile test run --rm service-tests python testing/evaluation/validate_benchmark_artifacts.py
```

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

Run evaluation with by-image queries:
```bash
docker compose --profile test run --rm service-tests \
  python testing/evaluation/run_evaluation.py \
  --base-url http://gateway-api:8000 \
  --by-image-queries testing/evaluation/by_image_queries.json
```

**Evaluation test suite:**
```bash
docker compose --profile test run --rm service-tests pytest testing/evaluation/test_evaluate_search.py testing/evaluation/test_full_evaluation.py testing/evaluation/test_benchmark_validation.py testing/evaluation/test_manifest_lock.py -v
```

The evaluation framework uses a locked local corpus (`testing/evaluation/assets/` — 35 assets: 30 images + 7 videos), a 120-query judged benchmark (`testing/evaluation/queries.json`), and saved baseline reports for regression detection. See `docs/metrics/search_tuning_checklist.md` for the full tuning workflow.

**Metric semantics:**
- Headline P@10/R@10/MRR/NDCG@10 are computed over **positive queries only**; negatives feed only the negative summary
- Video-granularity scene credit (E5): `relevant_scene_ids` like `scene:vid-foo.webm:0` match **any** scene of the same video — not the exact index
- P@10 is capped by corpus size (max ~0.35 on 35 assets); prefer Recall/MRR/NDCG for sensitivity
- Metrics naming: P@10, R@10, MRR, NDCG@10

### Smoke Testing (from repo root)

Run the end-to-end smoke test through Docker (requires stack running):
```bash
docker compose --profile test run --rm service-tests python testing/smoke_stack.py
```

This validates frontend reachability, gateway health/runtime, image upload, video upload, text search, image search, and delete using assets in `testing/smoke-assets/`.

### Frontend

Default frontend execution should go through Docker with the rest of the stack:
```bash
docker compose up -d --build frontend
```

If the user explicitly asks for local frontend-only work, the app also supports the standard Vite workflow from `frontend/`:
```bash
npm install
npm run dev
npm run build
npm run lint
npm test
```

Frontend is configured for Vitest with jsdom (see `vite.config.ts`), with `@testing-library/react` and `@testing-library/jest-dom`. The frontend targets `http://127.0.0.1:8000` (configured via `VITE_API_BASE_URL`). If frontend behavior changes, prefer validating it against the Dockerized stack.

**Frontend structure:**
- `src/pages/` — `SearchPage`, `LibraryPage`, `MediaDetailPage`, `DashboardPage`
- `src/components/` — `SearchResultCard`, `SearchResultGroup` (video-scene grouping), `MediaCard`, `MediaListPanel`, `UploadDropzone`, `UploadQueuePanel`, `RuntimeBadge`, `ThemeToggle`, `DataTable`, layout components
- `src/components/ui/` — design system primitives (`Button`, `Card`, `Dialog`, `Input`, `Select`, `Badge`, `Tabs`, `Skeleton`, `EmptyState`, `ErrorState`, `Sheet`)
- `src/utils/` — `searchResults.ts` (build render entries, group by media_id), `format.ts`
- `src/types/api.ts` — TypeScript types for API responses
- `src/api/client.ts` — API client
- `src/contexts/ThemeContext.tsx` — dark/light theme context
- `src/hooks/useKeyboardShortcuts.ts` — keyboard navigation

## Configuration

Key backend environment variables (see `docker-compose.yml` and `services/shared/semedia_shared/config.py` for defaults):
- `DATABASE_URL`: PostgreSQL connection string (SQLite in tests)
- `MEDIA_ROOT`, `MEDIA_BASE_URL`: File storage paths
- `ML_DEVICE`: `auto`, `cuda`, or `cpu`
- `ML_STRICT_CUDA`: `1` fails fast if CUDA is unavailable when expected
- `ML_PRELOAD_MODELS`: `1` preloads caption, CLIP, and rerank models during startup
- `CLIP_MODEL_NAME`: Default `openai/clip-vit-base-patch16`
- `CAPTION_MODEL_NAME`: Default `Salesforce/blip-image-captioning-large`
- `RERANK_MODEL_NAME`: Default `cross-encoder/ms-marco-MiniLM-L-6-v2`
- `SEARCH_RERANK_ENABLED`: `1` enables cross-encoder rerank (default `0` — OFF, measured to regress)
- `SCENE_DETECTION_THRESHOLD`: Base threshold default `27.0`
- `SCENE_FRAME_SAMPLE_COUNT`: Frames sampled per scene for multi-frame embedding default `3`
- `SEARCH_VECTOR_WEIGHT`, `SEARCH_KEYWORD_WEIGHT`: Hybrid fusion weights (default `0.7` / `0.3`)
- `SEARCH_MAX_RESULTS`: Maximum results returned to the client (default `20`)
- `SEARCH_MAX_PER_MEDIA`: Diversity cap for scenes from the same media item (default `2`)
- `SEARCH_CANDIDATE_MULTIPLIER`: Multiplier for candidate pool size (default `3`)
- `SEARCH_MIN_SCORE`: Configurable relevance score floor applied after diversity (default `0.0`)
- `CAPTION_MAX_LENGTH`, `CAPTION_MIN_LENGTH`, `CAPTION_NUM_BEAMS`, `CAPTION_RETRY_WEAK`, `CAPTION_RETRY_NUM_BEAMS`, `CAPTION_BATCH_SIZE`, `CAPTION_RETRY_FALLBACK`, `CAPTION_WEAK_MIN_WORDS`, `CAPTION_WEAK_MIN_CHARS`, `CAPTION_RETRY_MAX_LENGTH`, `CAPTION_RETRY_MIN_LENGTH`, `CAPTION_ENABLE_WEAK_FILTERING`: Caption quality and throughput settings
- `MEDIA_WORKER_URL`: Worker service URL for gateway and search-api
- `SEARCH_API_URL`: Search service URL for gateway
- `CORS_ALLOW_ALL_ORIGINS`: Enable permissive CORS for local development (default `1`)
- `LOG_LEVEL`, `LOG_FORMAT`: Logging configuration

Frontend configuration is in `frontend/.env` (copy from `.env.example`).

## Development Notes

**Current system state:**
- Phase 12 complete (2026-05-30) — accuracy audit remediation
- E5 (video-granularity scene credit): accepted, ON — R@10 0.98, MRR 0.87, NDCG@10 0.89
- C1 (cross-encoder rerank): implemented, default-OFF — measured to regress MRR 0.87→0.76
- B4 (BM25 keyword enrichment): deferred
- Accepted baseline: `testing/evaluation/baselines/baseline-phase7.json` (note: phase12-e5-c1 metrics recorded in history, but phase7 is the comparison baseline)

**Locked architecture decisions:**
- Backend: FastAPI
- Database: PostgreSQL (SQLite in tests only)
- Video segmentation: PySceneDetect with adaptive thresholds
- Captioning: Hugging Face BLIP image captioning pipeline
- Embeddings: CLIP `openai/clip-vit-base-patch16`
- Vector retrieval: local cosine search (no external vector DB yet)
- Keyword retrieval: durable TF-IDF artifacts persisted in the app
- Ranking semantics: normalized backend scores in `[0, 1]`, surfaced to the frontend with explanation metadata
- Reranking: heuristic boosts (exact phrase +0.08, rich caption +0.02) always active; cross-encoder optional, default-off (capture-only rerank discards CLIP visual signal)

**Workflow rules for this repo:**
- Prefer Docker-based execution for stack operations, backend tests, and evaluation work
- Prefer codegraph MCP tools for code exploration — codegraph provides a pre-built semantic index of the entire repo. It answers architecture/flow/symbol questions in 1-2 calls instead of dozens of grep+Read cycles. Fall back to manual Grep/Read only to confirm a specific detail codegraph didn't cover.
- **Tool selection by intent:**
  - "How does X work?" / "What's the deal with this area?" → `codegraph_context` (PRIMARY — single call surfaces entry points, related symbols, and key code)
  - "How does A reach B?" / "Trace the flow from X to Y" → `codegraph_trace` (ONE call returns full call path)
  - "Where is symbol X?" / "Find functions named like Y" → `codegraph_search`
  - "Show me several related symbols' source" → `codegraph_explore` (ONE capped call)
  - "Show me one symbol's signature/body/callers/callees" → `codegraph_node`
  - "What calls this?" → `codegraph_callers` | "What does this call?" → `codegraph_callees`
- For long coding tasks, split independent work across multiple subagents and monitor their progress
- Keep search-quality tracking updated when work changes the evaluation baseline or tuning state
- If search behavior changes materially, rerun the relevant evaluation commands and update `docs/metrics/search_quality_history.md`
- Use `testing/evaluation/baselines/baseline-phase7.json` as the current accepted baseline unless the user asks to replace it

**Code style:**
- Python: 4-space indentation, snake_case for functions/variables
- Frontend: 2-space indentation, PascalCase for components, camelCase for hooks/utilities
- Follow the existing feature-oriented frontend structure (pages, components, api, utils, types)

**Testing strategy:**
- Backend: pytest with isolated fixtures per service, SQLite for tests, CPU-only ML in tests, lighter models (clip-vit-base-patch32, blip-base)
- Evaluation: comprehensive pytest suite covering evaluate_search, full_evaluation, benchmark_validation, manifest_lock; Docker-run offline benchmark against locked corpus and judged query set
- Frontend: Vitest + Testing Library configured with component tests for SearchResultCard, SearchResultGroup, SearchPage, and searchResults utilities
- Smoke tests: end-to-end validation with real assets in `testing/smoke_stack.py`

**Security and hygiene:**
- Do not commit secrets, model weights, build artifacts, or uploaded media outside the intentional locked evaluation corpus
- Do not add ad hoc temp files under `testing/evaluation/assets/`; keep that corpus locked and intentional
- Use `.env` files for configuration and keep Docker-only/test artifacts cleaned up after one-off runs when possible
- Avoid creating new repo-level planning documents outside `docs/`.
