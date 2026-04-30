# Phase 2: Improve Processing Performance

## Context

Phase 1 established baseline metrics showing all search quality metrics at 0.0 due to poor caption quality. Phase 2 addresses processing performance by:

1. Adding adaptive scene detection thresholds based on video duration
2. Implementing batched caption generation (8 images per batch)
3. Implementing batched CLIP embedding inference (8 images per batch)

This phase improves processing throughput and scene detection quality without adding schema complexity.

## Schema Design

No schema changes in Phase 2. The existing single-frame scene model remains:

**MediaItem:**
- `caption: Text` - display caption
- `embedding: JSON[list[float]]` - CLIP embedding

**VideoScene:**
- `keyframe_path: String` - single keyframe per scene
- `thumbnail_path: String` - single thumbnail per scene
- `caption: Text` - scene caption
- `embedding: JSON[list[float]]` - scene CLIP embedding

## Implementation Steps

### Step 1: Implement adaptive scene detection

**Files to modify:**
- `services/shared/semedia_shared/video_service.py`

**Tasks:**
1. Add `_get_adaptive_threshold(duration: float, base_threshold: float) -> float`:
   - If duration < 30s: return 20.0
   - If duration > 600s (10 min): return 35.0
   - Otherwise: return base_threshold
2. Update `detect_scenes()` to use adaptive threshold:
   - Get video duration first
   - Calculate adaptive threshold
   - Pass to ContentDetector

**Verification:**
- Short videos (<30s) use threshold 20.0
- Long videos (>10min) use threshold 35.0
- Normal videos use configured threshold

### Step 2: Add batched caption generation

**Files to modify:**
- `services/shared/semedia_shared/caption_service.py`

**Tasks:**
1. Update `generate_captions()`:
   - Replace per-image loop with batched processing
   - Load all images into one processor batch
   - Run one model.generate() call per batch
   - Decode all outputs at once
   - Add chunking (8 images per batch) to prevent memory spikes
   - Keep function signature unchanged
2. Preserve fallback behavior when model loading/inference fails

**Verification:**
- Same API, better throughput
- Batch size prevents GPU/CPU memory issues
- Deterministic fallback still works
- Results order matches input order

### Step 3: Add batched CLIP embedding inference

**Files to modify:**
- `services/shared/semedia_shared/clip_service.py`

**Tasks:**
1. Update `encode_images()`:
   - Replace per-image loop with batched processing
   - Process images in chunks (8 images per batch)
   - Run one model.get_image_features() call per chunk
   - Keep function signature unchanged
2. Preserve fallback behavior when model loading/inference fails

**Verification:**
- Same API, better throughput
- Batch size prevents GPU/CPU memory issues
- Deterministic fallback still works
- Results order matches input order

## Critical Files

- `Semedia/services/shared/semedia_shared/video_service.py` - adaptive thresholds
- `Semedia/services/shared/semedia_shared/caption_service.py` - batch captions
- `Semedia/services/shared/semedia_shared/clip_service.py` - batch embeddings

## Verification Strategy

### Automated Tests

1. **Video service tests:**
   - Adaptive threshold: <30s → 20.0, >10min → 35.0, else base
   - Scene detection uses adaptive threshold

2. **Caption/CLIP service tests:**
   - Batch processing returns correct number of results
   - Results order matches input order
   - Fallback behavior preserved

3. **Pipeline tests:**
   - Images set caption and embedding
   - Videos create one frame per scene
   - Video caption aggregates scene captions

### Manual Verification

1. Upload and process new image and video
2. Inspect database rows:
   - One scene frame per scene
   - Caption and embedding populated
3. Test search:
   - Keyword search uses caption
   - Results display correctly
4. Run Phase 1 evaluation script to confirm metrics improve

### End-to-End Test

```bash
# From Semedia/
docker compose up --build gateway-api frontend

# Upload test media
python testing/smoke_stack.py

# Verify processing
curl http://127.0.0.1:8000/api/v1/media/ | jq '.results[] | {id, caption}'

# Test search
curl -X POST http://127.0.0.1:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query_text": "cat", "top_k": 10}' | jq '.results[0]'

# Re-run evaluation
docker compose run --rm service-tests python testing/evaluation/evaluate_search.py
```

## Success Criteria

- ✅ Adaptive scene detection thresholds based on duration
- ✅ Batched caption generation (8 images per batch)
- ✅ Batched CLIP embedding inference (8 images per batch)
- ✅ Processing throughput improved
- ✅ All tests pass
- ✅ Phase 1 evaluation metrics improve

## Risks and Mitigations

**Risk:** Batch processing increases memory usage
**Mitigation:** Use fixed batch size (8), chunk large video processing

**Risk:** Test breakage
**Mitigation:** Update tests in lockstep with implementation

## Next Steps After Phase 2

Phase 3 will build persistent TF-IDF index using caption fields, eliminating per-query corpus rebuilding and stabilizing keyword search scores.
