# V1 Architecture Lock

This document is the implementation baseline for the new `Semedia/` application.

## Locked Decisions

- Backend: Django + Django REST Framework
- Metadata store: PostgreSQL in app environments, SQLite in tests only
- Processing execution: local app-managed execution for MVP
- Video segmentation: PySceneDetect
- Captioning: BLIP-2 via Hugging Face Transformers
- Embeddings: CLIP `openai/clip-vit-base-patch32`
- Vector retrieval: local cosine search for MVP
- Keyword retrieval: TF-IDF over generated captions
- Indexed units:
  - images are indexed directly from `Media`
  - videos are indexed through `VideoScene`

## Phase 0 and 1 Boundaries

- Phase 0 establishes environment validation, benchmark tooling, and architecture lock.
- Phase 1 implements the backend foundation: media models, upload APIs, media lifecycle, cleanup, and minimal processing hooks.
- Phase 2 will add scene detection, captioning, embeddings, and index updates.

## Data Model Direction

- `Media`
  - original file
  - media type
  - processing status
  - duration
  - caption placeholder
  - stable retrieval key
- `VideoScene`
  - parent `Media`
  - scene order
  - start and end timestamps
  - keyframe and thumbnail files
  - caption placeholder
  - stable retrieval key

## Compatibility Policy

`SemaMedia-prev/` is preserved only for reference. New backend implementation should not preserve previous API or model choices unless they match the locked design.

## Deferred Infrastructure

- Redis and Celery are intentionally deferred until after MVP.
- Distributed workers, queue durability, and throughput optimization are post-MVP concerns.
- FAISS or any dedicated vector index is deferred until local search is too slow for MVP needs.
