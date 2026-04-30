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
- `CLIP_MODEL_NAME` accepts Hugging Face `CLIPModel` checkpoints such as `openai/clip-vit-base-patch32` (default), `openai/clip-vit-base-patch16`, `openai/clip-vit-large-patch14`, `openai/clip-vit-large-patch14-336`, `laion/CLIP-ViT-B-32-laion2B-s34B-b79K`, and `laion/CLIP-ViT-L-14-laion2B-s32B-b82K`.
- `CAPTION_MODEL_NAME` accepts Hugging Face BLIP and BLIP-2 checkpoints. Verified options include `Salesforce/blip-image-captioning-base` (default), `Salesforce/blip-image-captioning-large`, `Salesforce/blip2-opt-2.7b`, `Salesforce/blip2-opt-6.7b`, and `Salesforce/blip2-flan-t5-xl`.
- Automatic GPU selection still requires the host drivers and Docker runtime to expose the GPU inside the `media-worker` container.

### ML Model Options

The worker currently loads caption and embedding models through Hugging Face Transformers:

- CLIP embeddings use `transformers.CLIPModel` and `transformers.CLIPProcessor`, so `CLIP_MODEL_NAME` should point to a CLIP-compatible checkpoint.
- Caption generation uses `transformers.BlipForConditionalGeneration` or `transformers.Blip2ForConditionalGeneration`, selected by whether the model name contains `blip2`.
- BLIP-2 models are substantially heavier than BLIP models and are best used on CUDA; this worker attempts 8-bit quantized loading for BLIP-2 on GPU before falling back to fp16.

Recommended CLIP model choices:

- `openai/clip-vit-base-patch32`: fastest default, good general-purpose baseline, about `~600MB` VRAM for fp16 inference.
- `openai/clip-vit-base-patch16`: same family with smaller patches and slightly higher cost, about `~600MB` VRAM.
- `openai/clip-vit-large-patch14`: stronger retrieval quality with higher VRAM use, about `~1.7GB` VRAM.
- `openai/clip-vit-large-patch14-336`: largest verified option here, best if you can afford the extra memory, about `~1.7GB` VRAM.
- `laion/CLIP-ViT-B-32-laion2B-s34B-b79K`: OpenCLIP base alternative trained on LAION-2B, about `~600MB` VRAM.
- `laion/CLIP-ViT-L-14-laion2B-s32B-b82K`: OpenCLIP large alternative with higher quality and memory cost, about `~1.7GB` VRAM.

Recommended caption model choices:

- `Salesforce/blip-image-captioning-base`: fastest default, about `~900MB` VRAM for fp16 inference.
- `Salesforce/blip-image-captioning-large`: better captions with higher memory and latency, about `~1.9GB` VRAM.
- `Salesforce/blip2-opt-2.7b`: stronger captions, about `~3.5GB` VRAM with 8-bit quantization or `~5.5GB` in fp16.
- `Salesforce/blip2-opt-6.7b`: highest cost option in this list, about `~7GB` VRAM with 8-bit quantization or `~13GB` in fp16.
- `Salesforce/blip2-flan-t5-xl`: BLIP-2 option based on Flan-T5 instead of OPT, about `~4GB` VRAM with 8-bit quantization or `~6GB` in fp16.

These numbers are practical estimates for inference only and can vary with batch size, image resolution, CUDA allocator overhead, and whether the worker falls back from 8-bit to fp16 for BLIP-2.

See `Semedia/.env.example` for the same model list inline next to the configurable variables.

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
