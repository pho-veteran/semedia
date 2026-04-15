# Service Extraction

This directory contains the new MVP microservice split.

- `gateway_api/`: public HTTP surface for upload, media detail/list, runtime, and search proxying.
- `media_worker/`: internal processing service for scene detection, captioning, embeddings, and runtime diagnostics.
- `search_api/`: internal retrieval service for hybrid semantic + TF-IDF ranking.
- `shared/`: shared SQLAlchemy models, storage helpers, AI helpers, processing pipeline, and search logic.

Current rule: keep the frontend-facing API stable at `/api/v1/...` through `gateway_api`.
