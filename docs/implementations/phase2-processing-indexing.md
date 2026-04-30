# Phase 2: Improve Processing and Indexing

## Context

Phase 1 established baseline metrics showing all search quality metrics at 0.0 due to poor caption quality. Phase 2 addresses the root causes by:

1. Separating retrieval text from display captions
2. Improving video-level caption aggregation across multiple scenes
3. Implementing multi-frame scene sampling (3 frames per scene at 10%, 50%, 90%)
4. Adding adaptive scene detection thresholds based on video duration
5. Providing a reprocessing path for existing media

This phase makes indexed media representations more descriptive and stable, setting the foundation for Phase 3's persistent TF-IDF index and Phase 5's ranking improvements.

## Schema Design

### Approach: Additive JSON columns on VideoScene

Use JSON columns for multi-frame data rather than a new child table because:
- Project already uses JSON/JSONB for embeddings with SQLite/Postgres compatibility
- Fixed small frame set (3 frames) doesn't benefit from separate table joins
- Current search/serialization operates at scene granularity, not frame granularity
- Keeps migration simpler and preserves existing query patterns

### New Fields

**MediaItem:**
- `retrieval_text: Text` - richer text for TF-IDF indexing, separate from display caption

**VideoScene:**
- `retrieval_text: Text` - scene-level retrieval text (de-duplicated frame captions)
- `keyframe_paths: JSON[list[str]]` - 3 keyframe paths per scene
- `thumbnail_paths: JSON[list[str]]` - 3 thumbnail paths per scene
- `captions: JSON[list[str]]` - 3 captions per scene
- `embeddings: JSON[list[list[float]]]` - 3 embeddings per scene
- `best_frame_index: Integer | None` - which frame to use for display (default: 1 = midpoint)

**Compatibility strategy:**
- Keep existing singular fields (`caption`, `embedding`, `keyframe_path`, `thumbnail_path`) during Phase 2
- Populate them from `best_frame_index` for backward compatibility
- Defer dropping legacy columns to a future phase after full reprocessing

### Aggregation Rules

**Scene level:**
- Display `caption`: caption at `best_frame_index` (default index 1 = midpoint frame)
- `retrieval_text`: de-duplicated join of all non-empty frame captions
- `embedding`: mean of 3 normalized frame embeddings, then renormalize
- `keyframe_path`/`thumbnail_path`: paths at `best_frame_index`

**Video level:**
- Display `caption`: concise join of first few representative scene captions
- `retrieval_text`: de-duplicated join of multiple scene retrieval texts

## Migration Strategy

Current state: No Alembic, uses `Base.metadata.create_all()` at startup.

**Approach:** Add lightweight migration runner without introducing full Alembic mid-phase.

1. Create `schema_migrations` table to track applied migrations
2. Add versioned migration functions in new `migrations.py` module
3. Update `init_database()` to run pending migrations after `create_all()`
4. Implement Phase 2 migration as additive-only:
   - Add new columns with defaults
   - Backfill from existing data where possible
   - Keep old columns intact

**Backfill logic:**
- `retrieval_text = caption`
- `keyframe_paths = [keyframe_path]` if present
- `thumbnail_paths = [thumbnail_path]` if present
- `captions = [caption]` if present
- `embeddings = [embedding]` if present
- `best_frame_index = 0`

## Implementation Steps

### Step 1: Add migration infrastructure and schema

**Files to modify:**
- `services/shared/semedia_shared/database.py`
- `services/shared/semedia_shared/models.py`
- `services/shared/semedia_shared/migrations.py` (new)

**Tasks:**
1. Add `schema_migrations` table model
2. Create `migrations.py` with:
   - `get_applied_migrations()` - query applied versions
   - `apply_migration()` - run and record one migration
   - `run_pending_migrations()` - apply all pending
   - `migration_001_phase2_fields()` - Phase 2 schema changes
3. Update `MediaItem` model:
   - Add `retrieval_text: Mapped[str] = mapped_column(Text, default="")`
4. Update `VideoScene` model:
   - Add `retrieval_text: Mapped[str] = mapped_column(Text, default="")`
   - Add `keyframe_paths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)`
   - Add `thumbnail_paths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)`
   - Add `captions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)`
   - Add `embeddings: Mapped[list[list[float]] | None] = mapped_column(JSON, nullable=True)`
   - Add `best_frame_index: Mapped[int | None] = mapped_column(Integer, nullable=True)`
5. Update `init_database()` to call `run_pending_migrations()` after `create_all()`

**Verification:**
- New database gets all Phase 2 columns
- Existing database gains new columns via migration
- Migration is idempotent (safe to run multiple times)
- Test with both SQLite and Postgres

### Step 2: Update serialization and storage for compatibility

**Files to modify:**
- `services/shared/semedia_shared/serialization.py`
- `services/shared/semedia_shared/storage.py`

**Tasks:**
1. Update scene serialization to use `best_frame_index`:
   - Display caption from `captions[best_frame_index]` if available, else `caption`
   - Thumbnail URL from `thumbnail_paths[best_frame_index]` if available, else `thumbnail_path`
2. Update `delete_media_files()` to handle multi-frame paths:
   - Delete all files in `keyframe_paths` array if present
   - Delete all files in `thumbnail_paths` array if present
   - Fallback to singular `keyframe_path`/`thumbnail_path` for old rows
3. Keep API response shape unchanged (no new fields exposed yet)

**Verification:**
- API responses remain stable for existing frontend
- File deletion removes all scene frames, not just one
- Works for both pre-Phase-2 and post-Phase-2 rows

### Step 3: Implement adaptive scene detection and multi-frame extraction

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
3. Replace `extract_scene_keyframe()` with `extract_scene_keyframes()`:
   - Takes scene span, returns 3 frame path pairs
   - Sample at 10%, 50%, 90% of scene duration
   - Use deterministic filenames: `scene_{idx:04d}_frame_{frame_idx:02d}.jpg`
   - Return `(keyframe_paths: list[str], thumbnail_paths: list[str])`
   - Set midpoint frame (index 1) as default best frame

**Verification:**
- Short videos (<30s) use threshold 20.0
- Long videos (>10min) use threshold 35.0
- Normal videos use configured threshold
- Each scene produces exactly 3 keyframe/thumbnail pairs
- Filenames are deterministic and sortable

### Step 4: Add true batch processing to caption and CLIP services

**Files to modify:**
- `services/shared/semedia_shared/caption_service.py`
- `services/shared/semedia_shared/clip_service.py`

**Tasks:**
1. Update `generate_captions()`:
   - Replace per-image loop with batched processing
   - Load all images into one processor batch
   - Run one model.generate() call per batch
   - Decode all outputs at once
   - Add chunking (e.g., 8 images per batch) to prevent memory spikes
   - Keep function signature unchanged
2. Update `encode_images()`:
   - Replace per-image loop with batched processing
   - Process images in chunks
   - Run one model.get_image_features() call per chunk
   - Keep function signature unchanged
3. Preserve fallback behavior when model loading/inference fails

**Verification:**
- Same API, better throughput
- Batch size prevents GPU/CPU memory issues
- Deterministic fallback still works
- Results order matches input order

### Step 5: Refactor pipeline to populate new fields and aggregate

**Files to modify:**
- `services/shared/semedia_shared/pipeline.py`

**Tasks:**

**For images (`_process_image`):**
1. Set `media.caption` as today
2. Set `media.retrieval_text = media.caption`
3. Keep `media.embedding` unchanged

**For videos (`_process_video`):**
1. Detect scenes with adaptive threshold
2. Extract 3 frames per scene using new `extract_scene_keyframes()`
3. Flatten all scene-frame paths into single lists for batch processing
4. Call `generate_captions(settings, all_frame_paths)`
5. Call `encode_images(settings, all_frame_paths)`
6. Re-group outputs back into per-scene lists (3 captions, 3 embeddings per scene)
7. For each VideoScene, populate:
   - `keyframe_paths`, `thumbnail_paths`, `captions`, `embeddings`
   - `best_frame_index = 1` (midpoint frame)
   - Derived singular fields from best_frame_index:
     - `caption = captions[1]`
     - `embedding = mean(embeddings)` (normalized)
     - `keyframe_path = keyframe_paths[1]`
     - `thumbnail_path = thumbnail_paths[1]`
   - `retrieval_text = " ".join(unique non-empty captions)`
   - `index_key` as today
8. For MediaItem, build:
   - Display `caption`: join first 3 distinct scene captions, max 200 chars
   - `retrieval_text`: join first 10 distinct scene retrieval_texts, max 1000 chars
   - `index_key` as today

**Verification:**
- Images populate retrieval_text
- Videos create 3 frames per scene
- Scene singular fields match best_frame_index
- Scene retrieval_text is richer than display caption
- Video caption is concise, retrieval_text is comprehensive
- All new fields populated for newly processed media

### Step 6: Switch keyword search to retrieval_text

**Files to modify:**
- `services/shared/semedia_shared/search_service.py`

**Tasks:**
1. Update `_keyword_results()` corpus building:
   - For images: use `media.retrieval_text` if present, else `media.caption`
   - For scenes: use `scene.retrieval_text` if present, else `scene.caption`
2. Keep response `caption` field as display text (unchanged)
3. Keep vector search using singular `embedding` field (unchanged)

**Verification:**
- Keyword corpus uses retrieval_text for ranking
- API responses still return display caption
- Search results format unchanged
- Fallback to caption works for old rows

### Step 7: Add reprocessing utility

**Files to create:**
- `services/shared/semedia_shared/reprocess.py` (new)
- `testing/reprocess_media.py` (new CLI script)

**Tasks:**
1. Create `reprocess_media(settings, session, media_ids: list[int])` function:
   - For each media_id, call `process_media()` to regenerate everything
   - Log progress and errors
   - Make idempotent and resumable
2. Create CLI script that:
   - Accepts `--status` filter (default: COMPLETED)
   - Accepts `--media-ids` for specific items
   - Accepts `--batch-size` for chunked processing
   - Runs migration first
   - Reprocesses selected media
   - Reports summary statistics
3. Add documentation in `docs/` for running reprocessing

**Verification:**
- Script runs migration before reprocessing
- Existing media gets new fields populated
- 3 scene frames generated for old videos
- Script is resumable if interrupted
- Batch processing prevents memory issues

## Critical Files

- `Semedia/services/shared/semedia_shared/models.py` - schema changes
- `Semedia/services/shared/semedia_shared/database.py` - migration runner
- `Semedia/services/shared/semedia_shared/migrations.py` - migration logic (new)
- `Semedia/services/shared/semedia_shared/pipeline.py` - processing logic
- `Semedia/services/shared/semedia_shared/video_service.py` - multi-frame extraction
- `Semedia/services/shared/semedia_shared/caption_service.py` - batch captions
- `Semedia/services/shared/semedia_shared/clip_service.py` - batch embeddings
- `Semedia/services/shared/semedia_shared/search_service.py` - retrieval_text usage
- `Semedia/services/shared/semedia_shared/serialization.py` - response compatibility
- `Semedia/services/shared/semedia_shared/storage.py` - multi-file deletion
- `Semedia/services/shared/semedia_shared/reprocess.py` - reprocessing utility (new)
- `Semedia/testing/reprocess_media.py` - CLI script (new)

## Verification Strategy

### Automated Tests

1. **Migration tests:**
   - New DB includes Phase 2 columns
   - Existing DB migration adds columns and preserves data
   - Migration is idempotent

2. **Video service tests:**
   - Adaptive threshold: <30s → 20.0, >10min → 35.0, else base
   - Multi-frame extraction returns 3 ordered path pairs
   - Filenames are deterministic

3. **Caption/CLIP service tests:**
   - Batch processing returns correct number of results
   - Results order matches input order
   - Fallback behavior preserved

4. **Pipeline tests:**
   - Images set retrieval_text
   - Videos create 3 frames per scene
   - Scene fields match best_frame_index
   - Video aggregation populates both caption and retrieval_text

5. **Search tests:**
   - Keyword search uses retrieval_text
   - API returns display caption
   - Results format unchanged

6. **Storage tests:**
   - Deleting video removes all frame files
   - Works for both old and new schema rows

### Manual Verification

1. Run migration on test database copy
2. Upload and process new image and video
3. Inspect database rows:
   - New columns populated
   - 3 scene frames per scene
   - retrieval_text richer than caption
4. Test search:
   - Keyword search uses retrieval_text
   - Results display correctly
5. Run reprocessing script on small sample
6. Delete media and verify all files removed
7. Run Phase 1 evaluation script to confirm metrics improve

### End-to-End Test

```bash
# From Semedia/
docker compose up --build gateway-api frontend

# Upload test media
python testing/smoke_stack.py

# Verify processing
curl http://127.0.0.1:8000/api/v1/media/ | jq '.results[] | {id, caption, retrieval_text}'

# Test search
curl -X POST http://127.0.0.1:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query_text": "cat", "top_k": 10}' | jq '.results[0]'

# Run reprocessing
docker compose run --rm service-tests python testing/reprocess_media.py --status COMPLETED

# Re-run evaluation
docker compose run --rm service-tests python testing/evaluation/evaluate_search.py
```

## Success Criteria

- ✅ `retrieval_text` exists for all completed images and scenes
- ✅ Video-level text derived from multiple scenes, not just first
- ✅ Scene representations use 3 frames per scene
- ✅ Adaptive scene detection thresholds based on duration
- ✅ Migration runs successfully on existing databases
- ✅ Reprocessing script successfully upgrades existing media
- ✅ Search uses retrieval_text for keyword ranking
- ✅ API responses remain backward compatible
- ✅ All tests pass
- ✅ Phase 1 evaluation metrics improve after reprocessing

## Risks and Mitigations

**Risk:** Breaking existing API responses
**Mitigation:** Keep singular fields populated from best_frame_index, don't expose new fields in Phase 2

**Risk:** Storage cleanup misses files
**Mitigation:** Update deletion to iterate arrays first, fallback to singular fields

**Risk:** 3x frame extraction increases processing time
**Mitigation:** Batch inference, chunk processing, make reprocessing resumable

**Risk:** Migration fails on existing databases
**Mitigation:** Additive-only migration, extensive testing, idempotent design

**Risk:** Test breakage
**Mitigation:** Update tests in lockstep with implementation

## Next Steps After Phase 2

Phase 3 will build persistent TF-IDF index using the new `retrieval_text` fields, eliminating per-query corpus rebuilding and stabilizing keyword search scores.
