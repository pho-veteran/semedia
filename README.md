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

The default worker installs CUDA-capable PyTorch, preloads its caption and CLIP models during startup, prefers GPU automatically with `ML_DEVICE=auto`, and runs in strict CUDA mode in Docker Compose.
The worker image also installs `torchvision`, enabling the faster Hugging Face image processors used by the caption and CLIP pipelines.

## Configuration

Selected backend environment variables:

- `LOG_LEVEL` controls the Python service log level and defaults to `INFO`.
- `LOG_FORMAT` reserves the log output mode and defaults to `text`, which writes readable logs to stdout.
- `ML_DEVICE` defaults to `auto`, which selects CUDA when `torch.cuda.is_available()` is true and otherwise uses CPU.
- `ML_STRICT_CUDA=1` makes startup fail fast when the worker cannot access CUDA as expected.
- `ML_PRELOAD_MODELS=1` preloads and probes the caption and CLIP pipelines during worker startup so the first live request does not pay cold-start latency.
- Automatic GPU selection still requires the host drivers and Docker runtime to expose the GPU inside the `media-worker` container.

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
