# Semedia

Semedia is the active semantic media search app. It runs as a small local microservice stack and preserves the frontend contract on `http://127.0.0.1:8000/api/v1/...`.

## Active Services

```text
Semedia/
  services/
    gateway_api/   # Public upload, media, runtime, and search proxy API
    media_worker/  # Scene detection, captioning, embeddings, GPU-bound work
    search_api/    # Hybrid retrieval and ranking
    shared/        # Shared SQLAlchemy models and processing/search logic
  frontend/        # Active React + TypeScript frontend
  testing/         # Active service tests, smoke tests, and smoke assets
  docs/            # Active implementation notes
```

## Docker Compose

Run from `Semedia/`:

```bash
docker compose up --build gateway-api frontend
docker compose ps
curl http://127.0.0.1:8000/api/v1/runtime/
```

Default services:
- `db`
- `media-worker`
- `search-api`
- `gateway-api`
- `frontend`

The default worker is GPU-backed and runs with `ML_DEVICE=cuda` plus `ML_STRICT_CUDA=1`.

## Service Notes

- `gateway-api` keeps the frontend-facing API stable.
- `media-worker` owns scene extraction, captioning, and embeddings.
- `search-api` owns hybrid ranking and calls the worker only for query text embeddings.
- `shared/` holds the common database models, storage helpers, pipeline code, and search helpers used by the services.

## Testing

Run the active service tests from `Semedia/`:

```bash
docker compose --profile test run --rm --build service-tests
python testing/smoke_stack.py
```

The smoke flow uses assets in `Semedia/testing/smoke-assets/` and validates frontend reachability, gateway health/runtime, image upload, video upload, search, and delete.

## Frontend

Run frontend commands from `Semedia/frontend/`:

```bash
copy .env.example .env
npm run dev
npm run build
npm run lint
```

The frontend targets `http://127.0.0.1:8000`.
