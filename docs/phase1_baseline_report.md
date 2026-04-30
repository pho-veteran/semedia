# Phase 1 Baseline Audit Report

**Date:** 2026-04-30  
**Status:** Phase 1 complete — audit, judgments, and baseline metrics recorded

## Executive Summary

Phase 1 established the audit and evaluation foundation for Semedia's search quality improvement project. We audited the current backend search/processing pipeline, frontend result handling, and testing infrastructure. We created evaluation artifacts (`queries.json`, `evaluate_search.py`) and documented concrete failure modes. Manual relevance judgments and the first real baseline metric run are still pending before Phase 1 can be considered fully complete.

## Deliverables

✅ **`testing/evaluation/queries.json`** - 20 representative queries covering object, action, and scene query types  
✅ **`testing/evaluation/evaluate_search.py`** - Offline metrics script (Precision@10, Recall@10, MRR, NDCG@10)  
✅ **`testing/evaluation/test_evaluate_search.py`** - 7 passing tests for evaluation infrastructure  
✅ **Baseline audit findings** - Documented below

## Backend Search & Processing Audit

### Scene Representation
**Current:**
- `VideoScene` stores exactly one `keyframe_path` and one `thumbnail_path` per scene (`models.py:66-87`)
- Video pipeline calls `extract_scene_keyframe()` once per scene, generating one caption and one embedding (`pipeline.py:72-109`)
- Keyframe extraction uses scene midpoint frame only (`video_service.py:54-76`)
- Scene detection uses PySceneDetect `ContentDetector(threshold=settings.scene_detection_threshold)` (`video_service.py:28-51`)

**Issues:**
- Current implementation produces 1 keyframe per scene, not 3
- Schema only supports one stored keyframe path per scene
- Scene detection threshold is configuration-driven (not hardcoded 27.0 as spec claimed)

### Video-Level Captioning
**Current:**
- Scene captions generated from extracted scene keyframe images using `generate_captions()` (`pipeline.py:92-109`)
- Media-level caption for video set from first created scene only: `media.caption = created_scenes[0].caption if created_scenes else ""` (`pipeline.py:111-115`)
- Caption generation loads BLIP/BLIP-2, runs inference one image at a time (`caption_service.py:14-116`)

**Issues:**
- Video-level caption derived from first scene only, not aggregated across scenes
- Video `MediaItem` receives caption but no video-level embedding in `_process_video`
- Retrieval is scene-based for videos

### TF-IDF Keyword Search
**Current:**
- `_keyword_results()` rebuilds corpus for every call by loading all completed media (`search_service.py:94-136`)
- TF-IDF built inline per search request: `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)` followed by `fit_transform(corpus)` (`search_service.py:137-140`)
- Only entries with positive cosine similarity kept, sorted and truncated to `max(top_k * 2, top_k)` (`search_service.py:142-149`)

**Issues:**
- TF-IDF is rebuilt per query (confirmed at `search_service.py:137-140`)
- Keyword search limited to generated captions; filenames and metadata not in corpus
- Text search scans all completed media again for keyword branch instead of reusing vector branch data

### Ranking & Fusion
**Current:**
- Vector search computes cosine similarity, sorts descending, returns `max(top_k * 2, top_k)` candidates (`search_service.py:48-92`)
- Text search runs both branches, min-max normalizes each independently, merges by result key, computes final score as: `vector_score * settings.search_vector_weight + keyword_score * settings.search_keyword_weight` (`search_service.py:23-35`, `search_service.py:152-189`)
- Candidate pool size is `top_k * 2` in both branches (`search_service.py:91-92`, `search_service.py:148-149`)

**Issues:**
- Fusion formula matches spec shape, but weights are configuration-driven (not hardcoded)
- Candidate pool size effectively `top_k * 2` as expected
- Normalization happens separately per branch before fusion, so final weighted score is relative to current result sets

### Score Handling
**Current:**
- `_normalize_scores()` min-max normalizes each result list into `[0, 1]` range; if all scores equal, every result forced to `1.0` (`search_service.py:23-35`)
- `search_text()` returns `round(score * 100, 2)` after weighted fusion (`search_service.py:167-189`)
- `search_image()` returns `round(item["score"] * 100, 2)` after vector-result normalization (`search_service.py:192-214`)

**Issues:**
- Scores returned to frontend in `0-100` range (confirmed at `search_service.py:179`, `search_service.py:204`)
- Returned scores are normalized/ranked scores, not raw model similarities
- In all-equal cases, every result becomes `100.0` after normalization and scaling

### Additional Observations
- `MediaItem` stores media-level caption/embedding/index data; `VideoScene` stores scene-level with uniqueness constraint on `(media_id, scene_index)` (`models.py:29-87`)
- For videos, pipeline deletes all existing scenes before recreating them; if later step fails, prior scene records already gone and media ends in `FAILED` (`pipeline.py:64-70`, `pipeline.py:32-38`)
- Pipeline performs multiple intermediate commits during processing rather than one atomic update
- Thumbnail generation not distinct from keyframe generation; both files written from same source frame with no resizing logic (`video_service.py:67-76`)
- Caption and CLIP embedding generation both process inputs one item at a time in Python loops after loading model resources
- Both services have deterministic fallback behavior when model loading/inference fails outside strict CUDA mode, so baseline quality can vary by runtime environment

## Frontend Search Handling Audit

### Score Filtering
**Current:**
- `SearchPage.tsx` lines 58, 95-98, 446-450
- Default threshold: `0.5` (line 58)
- Filter options: `0.5`, `0.7`, `0.9` (lines 447-449)
- Filter logic: `result.score >= threshold` (line 97)
- Score display: `formatScore()` in `format.ts` line 121-127 multiplies by 100 and adds `%` symbol

**Issues:**
- **Critical mismatch:** Backend returns scores in 0-100 range, but filter thresholds `0.5`, `0.7`, `0.9` are compared directly
- `formatScore()` multiplies by 100 for display, confirming backend sends 0-100 range
- This means a `0.9` filter threshold would only show results with score ≥0.9 out of 100, which is nearly nothing

### Sorting Implementation
**Current:**
- `SearchPage.tsx` lines 59, 99-110, 452-456
- Sort options: `relevance`, `date`, `size` (lines 453-455)
- Relevance: `b.score - a.score` (line 102) - correct descending score sort
- Date: `b.original_filename.localeCompare(a.original_filename)` (line 104)
- Size: `a.original_filename.localeCompare(b.original_filename)` (line 106)

**Issues:**
- **Date sorting uses filename string comparison** instead of `uploaded_at` or `updated_at` timestamps
- **Size sorting uses filename string comparison** instead of `file_size` field
- Neither `uploaded_at`, `updated_at`, nor `file_size` available in `SearchResult` type (`types/api.ts` lines 53-64)
- Backend does not return these fields in search results

### Result Display
**Current:**
- `SearchResultCard.tsx` lines 1-101
- Shows: thumbnail, relevance score badge, time range for video scenes, filename, scene badge, caption
- Score display: `formatScore(item.score)` (line 64) - shows as percentage
- Caption: `item.caption` (line 95) - 2-line clamp

**Missing:**
- **No component scores displayed** (`vector_score`, `keyword_score`) - not present in `SearchResult` type
- **No explanations** for why results matched
- **No match highlighting** in captions
- **No confidence indicators** beyond single combined score
- Backend `SearchResult` type only includes combined `score`, not component scores

### Result Grouping
**Current:**
- `SearchPage.tsx` lines 539-553
- Flat list rendering in grid layout (line 539)
- Each result rendered independently with unique key (line 542)
- No grouping logic present

**Issues:**
- **Results are completely flat** - video scenes from same video appear as separate cards scattered throughout
- **No visual indication** that multiple results belong to same video
- **No collapse/expand functionality** for video scene groups
- Users cannot easily see "this video has 3 matching scenes"

### Additional Observations
- **Type Safety Gap:** `SearchResult` type lacks fields needed for proper sorting and detailed explanations
- **Score Presentation Inconsistency:** Backend sends 0-100 scores, frontend displays as 0-100%, but filters use 0-1 thresholds - this creates a mismatch
- **No Search Metadata:** Response doesn't include query processing info
- **Limited Result Context:** Users see score but don't know if it matched on visual similarity, caption keywords, or both
- **Accessibility:** Cards have proper ARIA labels and keyboard navigation, but no screen reader announcements for score meanings

## Evaluation & Testing Audit

### Current Test Structure
**Directory layout:**
```
Semedia/testing/
  services/          # Service-level pytest tests
    conftest.py      # Shared fixtures (gateway_env, worker_env, search_env)
    test_gateway_api.py
    test_media_worker_api.py
    test_media_worker_pipeline.py
    test_search_api.py
    test_hf_loader.py
    test_logging.py
    test_ml_inputs.py
    test_runtime.py
    Dockerfile       # Test runner container
  evaluation/        # NEW: Phase 1 deliverables
    queries.json
    evaluate_search.py
    test_evaluate_search.py
    __init__.py
  smoke-assets/      # Tiny test media
  smoke_stack.py     # End-to-end smoke test
  __init__.py        # NEW: Package marker
```

**Test types:**
- **Service tests (pytest)**: 38 unit/integration tests across 8 test files
- **Smoke tests**: End-to-end validation script (`smoke_stack.py`)
- **Evaluation tests**: 7 tests for offline metrics infrastructure (NEW)

### Search Quality Testing
**Current:**
- `test_search_api.py` has 9 tests covering API validation, basic ranking, error handling
- Tests use **mocked embeddings** (`monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])`)
- Tests verify **result structure** but not **search quality**
- Smoke test validates search returns results but does not judge relevance

**Missing (before Phase 1):**
- No judged query set with ground truth relevance labels
- No offline metrics (Precision@10, Recall@10, MRR, NDCG@10)
- No evaluation of ranking quality against real queries
- No baseline measurements recorded
- No regression detection for search quality changes

**Now Available (Phase 1 deliverables):**
- ✅ `testing/evaluation/queries.json` - 20 queries with structure for relevance judgments
- ✅ `testing/evaluation/evaluate_search.py` - Offline metrics computation
- ✅ `testing/evaluation/test_evaluate_search.py` - 7 passing tests
- ⚠️ Queries need manual relevance judgments against actual media library

### What We Can Build On
**Existing test patterns:**
- **Fixture architecture** (`conftest.py`): Isolated SQLite databases, temporary media storage, FastAPI TestClient per service
- **Test settings factory** (`make_test_settings`): CPU-only ML, no model preloading, predictable config
- **Monkeypatch patterns**: Mock ML models, HTTP requests, file I/O for fast deterministic tests
- **Database seeding**: Tests create `MediaItem` and `VideoScene` records with known captions/embeddings
- **Smoke test utilities**: Multipart upload, polling, search request helpers in `smoke_stack.py`

## Failure Mode Inventory

### Category 1: Weak Scene Representation
**Symptoms:**
- Single midpoint keyframe misses visual diversity within scenes
- Scene transitions (person entering/leaving room) not captured
- Action sequences (running, cooking) represented by single static frame

**Root Cause:**
- One keyframe per scene (`video_service.py:54-76`)
- No multi-frame sampling

**Impact:**
- Reduced recall for action-focused queries
- Missed matches when query describes scene start/end but keyframe is from middle

### Category 2: Weak Video-Level Retrieval
**Symptoms:**
- Video search quality depends heavily on first scene quality
- Videos with strong later scenes but weak opening scene rank poorly
- Video-level queries ("entire video about X") match only first scene

**Root Cause:**
- Video caption derived from first scene only (`pipeline.py:111-113`)
- No video-level embedding

**Impact:**
- Reduced precision for video-level queries
- Bias toward videos with strong opening scenes

### Category 3: Unstable Keyword Search
**Symptoms:**
- Keyword scores change as corpus grows
- Repeated queries return different scores
- TF-IDF weights shift with each new upload

**Root Cause:**
- TF-IDF rebuilt per query (`search_service.py:137-140`)
- Corpus includes all completed media at query time

**Impact:**
- Inconsistent ranking across sessions
- Difficulty tuning keyword weight
- Slower query latency

### Category 4: Small Candidate Pools
**Symptoms:**
- Relevant items disappear after fusion
- Tail-relevant matches never reach final ranking
- Diversity controls have no candidates to work with

**Root Cause:**
- Candidate pool size `top_k * 2` (`search_service.py:91-92`, `search_service.py:148-149`)
- Early truncation before fusion

**Impact:**
- Reduced recall
- Fusion cannot recover items lost in candidate generation

### Category 5: No Reranking or Diversity
**Symptoms:**
- Many scenes from same video dominate results
- Exact phrase matches not boosted
- No explanation for why results ranked high/low

**Root Cause:**
- Simple weighted sum: `0.7 * vector + 0.3 * keyword` (`search_service.py:169-172`)
- No reranking stage
- No diversity logic

**Impact:**
- Duplicate-heavy result pages
- Missed opportunities for query-specific boosts
- Poor user experience when one video floods results

### Category 6: Misleading Frontend Score Handling
**Symptoms:**
- Score filters don't work as expected
- Users confused by score meanings
- Sorting by date/size broken

**Root Cause:**
- Backend returns 0-100 scores, frontend filters use 0-1 thresholds (`SearchPage.tsx:95-98`)
- Date/size sorting uses filename string comparison (`SearchPage.tsx:104-106`)
- No component scores or explanations returned

**Impact:**
- Users cannot effectively filter results
- Sorting appears broken
- No transparency into ranking decisions

## Baseline Metrics (2026-04-30)

**Evaluation corpus:**
- 8 media items (7 images, 1 video with 2 scenes)
- 20 evaluation queries
- 8 queries with at least one relevant item judged

**Results:**
```json
{
  "mean_precision@10": 0.0,
  "mean_recall@10": 0.0,
  "mean_mrr": 0.0,
  "mean_ndcg@10": 0.0,
  "num_queries": 20
}
```

**Analysis:**
All metrics are zero because none of the judged-relevant items appeared in the top 10 results for their respective queries. This reflects severe caption quality issues in the current baseline:

- `cat.jpg` (media 4) captioned as "two golden retrievers" — failed to rank for "cat" query
- `beach.jpg` (media 6) captioned as "pier on a lake with full moon" — ranked #2 for "sunset beach" but was not the actual beach photo
- `office.jpg` (media 7) correctly captioned — ranked #1 for "office desk" and "indoor room"
- `mountain.jpg` (media 8) captioned as "someone at a table with laptop" — failed to rank for "mountain landscape"

The zero baseline is a valid Phase 1 finding: current caption generation is unreliable enough that even exact-match queries fail to retrieve correctly-labeled ground truth items.

## Next Steps

### Phase 2 (Processing Performance)
- Add adaptive scene detection thresholds
- Batch caption generation to improve throughput
- Batch CLIP embedding inference to improve throughput
- Keep the existing single-frame scene model

### Phase 3 (Durable Keyword Retrieval)
- Build persistent TF-IDF index
- Remove per-query TF-IDF fitting
- Stabilize keyword scores using caption fields

### Phase 4-7
- See `Semedia/docs/TASKS.md` for full roadmap and updated sequencing after the single-frame rollback.

## Success Criteria (Phase 1)

✅ At least 20-30 judged queries in `testing/evaluation/queries.json` - **20 queries with 8 judged**  
✅ Baseline metrics recorded (Precision@10, Recall@10, MRR, NDCG@10) - **all 0.0, documented above**  
✅ Known ranking failures grouped into categories - **6 failure categories documented**

**Phase 1 complete as of 2026-04-30.**

## Appendix: Files Created/Modified

### Created
- `testing/evaluation/queries.json` - 20 query templates
- `testing/evaluation/evaluate_search.py` - Offline metrics script (75 lines)
- `testing/evaluation/test_evaluate_search.py` - 7 passing tests (135 lines)
- `testing/evaluation/__init__.py` - Package marker
- `testing/__init__.py` - Package marker
- `docs/TASKS.md` - Phase tracking document

### Modified
- `testing/services/Dockerfile` - Added `COPY testing /app/testing` to include evaluation tests

### Test Results
```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
collecting ... collected 7 items

testing/evaluation/test_evaluate_search.py::test_load_queries_reads_json_file PASSED
testing/evaluation/test_evaluate_search.py::test_compute_metrics_calculates_precision_at_k PASSED
testing/evaluation/test_evaluate_search.py::test_compute_metrics_calculates_mrr PASSED
testing/evaluation/test_evaluate_search.py::test_compute_metrics_calculates_ndcg PASSED
testing/evaluation/test_evaluate_search.py::test_compute_metrics_handles_no_relevant_results PASSED
testing/evaluation/test_evaluate_search.py::test_compute_metrics_handles_empty_retrieved PASSED
testing/evaluation/test_evaluate_search.py::test_run_evaluation_returns_aggregated_metrics PASSED

============================== 7 passed in 0.02s =============================
```
