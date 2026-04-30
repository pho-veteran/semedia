# Search Quality Redesign

**Date:** 2026-04-30  
**Status:** Design approved, ready for implementation planning

## Executive Summary

This document specifies a comprehensive redesign of Semedia's search and ranking system to address systemic quality issues in data processing, retrieval, ranking, and result presentation. The current implementation uses weak scene representation, per-query TF-IDF fitting, simplistic score fusion, no reranking or diversity controls, and misleading UI score handling. This redesign transforms search from a single weighted sum into a proper multi-stage retrieval pipeline while preserving the MVP architecture (FastAPI, local search, no external vector DB).

## Problem Statement

### Current Architecture Weaknesses

**Data Processing & Indexing:**
- Videos use one midpoint keyframe per scene (`services/shared/semedia_shared/video_service.py:54`)
- Captions are single-shot BLIP-2 outputs with no enrichment
- Video-level `media.caption` is just the first scene caption (`services/shared/semedia_shared/pipeline.py:112`)
- No separation between display text and retrieval text
- Scene detection threshold is fixed at 27.0 with no adaptive logic

**Retrieval:**
- TF-IDF vectorizer is rebuilt on every query (`services/shared/semedia_shared/search_service.py:137`)
- Corpus includes all completed media, making TF-IDF unstable as library grows
- No query preprocessing or expansion
- Candidate pools are limited to `top_k * 2` per signal before fusion

**Ranking:**
- Simple weighted sum: `0.7 * vector_score + 0.3 * keyword_score` (`services/shared/semedia_shared/search_service.py:169`)
- No reranking stage
- No diversity or deduplication logic
- Scenes from the same video can dominate results

**Result Presentation:**
- Backend returns scores as `0-100` (`services/shared/semedia_shared/search_service.py:179`)
- Frontend applies score filters like `≥0.5` against these 0-100 scores (`frontend/src/pages/SearchPage.tsx:95`)
- No component score breakdown or explanations
- Client-side sorting by "date" and "size" uses filename string comparison, not actual metadata

**Testing & Evaluation:**
- Tests verify API contracts but not search quality
- No judged query set or offline metrics
- No way to measure improvement objectively

## Goals

1. **Improve indexing quality** so retrieval has better data to work with
2. **Stabilize retrieval** by precomputing keyword indexes and expanding candidate pools
3. **Add reranking and diversity** to produce better final result sets
4. **Fix result presentation** so scores and explanations are honest and useful
5. **Build evaluation infrastructure** so future tuning is evidence-based

## Design

### 1. Data Processing & Indexing Improvements

#### 1.1 Scene Representation

**Current:** One midpoint keyframe per scene.

**Proposed:** Multi-frame sampling per scene to capture visual diversity.

- Extract 3 keyframes per scene: start (10% into scene), middle (50%), end (90%)
- Generate captions for all 3 frames
- Generate embeddings for all 3 frames
- Store all frames and their captions/embeddings in `VideoScene`
- At search time, use the best-matching frame from each scene

**Why:** Scenes are not visually uniform. A scene transition might show a person entering a room (start), talking (middle), and leaving (end). Single midpoint sampling misses this diversity.

**Schema changes:**
```python
# VideoScene model additions
keyframe_paths: list[str]  # 3 paths instead of 1
thumbnail_paths: list[str]  # 3 thumbnails
captions: list[str]  # 3 captions
embeddings: list[list[float]]  # 3 embeddings
best_frame_index: int | None  # which frame matched query (set at search time)
```

**How to apply:** Update `services/shared/semedia_shared/video_service.py:extract_scene_keyframe()` to extract 3 frames. Update `services/shared/semedia_shared/pipeline.py:_process_video()` to batch-process all frames.

#### 1.2 Retrieval Text vs Display Text

**Current:** Single `caption` field used for both display and search.

**Proposed:** Separate fields for retrieval and display.

- `caption`: short, user-facing description (unchanged)
- `retrieval_text`: enriched text for search, combining:
  - generated caption
  - detected objects/entities (if available)
  - OCR text (if available)
  - filename tokens (sanitized)
  - parent video context for scenes

**Why:** Display captions should be concise. Retrieval text should be comprehensive. Conflating them limits both.

**Schema changes:**
```python
# MediaItem and VideoScene additions
retrieval_text: str  # comprehensive search text
```

**How to apply:** Update `services/shared/semedia_shared/pipeline.py` to populate `retrieval_text` after caption generation. For MVP, `retrieval_text = caption + " " + sanitized_filename`. Future: add OCR, object detection.

#### 1.3 Video-Level Aggregation

**Current:** `media.caption` is first scene caption.

**Proposed:** Video-level caption is a summary of all scene captions.

- Concatenate all scene captions
- For MVP: use first + middle + last scene captions
- Future: use LLM to generate video-level summary

**Why:** Video-level search should match video-level semantics, not just the first scene.

**How to apply:** Update `services/shared/semedia_shared/pipeline.py:_process_video()` to set `media.caption` and `media.retrieval_text` from aggregated scene text.

#### 1.4 Scene Detection Tuning

**Current:** Fixed threshold of 27.0.

**Proposed:** Adaptive threshold based on video characteristics.

- Default: 27.0
- For short videos (<30s): lower threshold (e.g., 20.0) to capture more scenes
- For long videos (>10min): higher threshold (e.g., 35.0) to avoid over-segmentation
- Store detected scene count and duration stats for analysis

**Why:** One threshold does not fit all video types. Short clips need finer segmentation; long videos need coarser cuts.

**How to apply:** Update `services/shared/semedia_shared/video_service.py:detect_scenes()` to adjust threshold based on video duration.

### 2. Retrieval Improvements

#### 2.1 Precomputed Keyword Index

**Current:** TF-IDF vectorizer is rebuilt on every query.

**Proposed:** Precompute and persist TF-IDF index.

- Build TF-IDF index from all `retrieval_text` fields
- Store vectorizer and document matrix in a persistent index file (e.g., `media_root/indexes/tfidf_index.pkl`)
- Rebuild index on media add/delete/reprocess
- Load index at service startup

**Why:** Per-query TF-IDF fitting is slow, unstable, and produces inconsistent scores as the corpus grows.

**Implementation:**
- Add `services/shared/semedia_shared/index_service.py` with `build_tfidf_index()`, `load_tfidf_index()`, `search_tfidf_index()`
- Add index rebuild trigger in `services/shared/semedia_shared/pipeline.py:process_media()`
- Add index loading in `services/search_api/app/main.py:lifespan()`

**Schema changes:**
```python
# MediaItem and VideoScene additions
tfidf_doc_id: int | None  # position in TF-IDF matrix
```

#### 2.2 Larger Candidate Pools

**Current:** Retrieve `top_k * 2` candidates per signal.

**Proposed:** Retrieve `top_k * 5` candidates per signal before fusion.

**Why:** Fusion and reranking need a larger pool to select from. Current pools are too small to recover from early ranking errors.

**How to apply:** Update `services/shared/semedia_shared/search_service.py:_vector_results()` and `_keyword_results()` to return `top_k * 5`.

#### 2.3 Query Preprocessing

**Current:** Query text is used as-is.

**Proposed:** Normalize and expand queries.

- Lowercase and strip
- Remove stop words for keyword search (but not for CLIP text encoding)
- Expand common abbreviations (e.g., "vid" → "video")
- Future: query expansion via synonyms or LLM

**Why:** User queries are noisy. Preprocessing improves recall.

**How to apply:** Add `services/shared/semedia_shared/query_service.py` with `preprocess_query()` and `expand_query()`.

### 3. Ranking Improvements

#### 3.1 Multi-Stage Ranking Pipeline

**Current:** Single weighted sum.

**Proposed:** 4-stage pipeline:

1. **Candidate generation:** Retrieve large pools from vector and keyword channels
2. **Fusion:** Combine signals with learned weights
3. **Reranking:** Apply business rules and quality signals
4. **Diversity:** Deduplicate and diversify final results

**Implementation:**
- Add `services/shared/semedia_shared/ranking_service.py` with `rank_candidates()`, `rerank_results()`, `diversify_results()`
- Update `services/shared/semedia_shared/search_service.py:search_text()` to call ranking pipeline

#### 3.2 Fusion Strategy

**Current:** `0.7 * vector + 0.3 * keyword`

**Proposed:** Weighted fusion with configurable weights and normalization.

- Normalize vector and keyword scores independently to [0, 1]
- Apply weights: `w_vector * vector_score + w_keyword * keyword_score + w_recency * recency_score`
- Default weights: `w_vector=0.6, w_keyword=0.3, w_recency=0.1`
- Make weights configurable via environment variables

**Why:** Current weights are arbitrary. Configurable weights allow tuning. Recency signal helps surface recent uploads.

**Schema changes:**
```python
# Settings additions
search_recency_weight: float  # default 0.1
```

**How to apply:** Update `services/shared/semedia_shared/search_service.py:search_text()` to compute recency score from `media.created_at` and apply weighted fusion.

#### 3.3 Reranking Rules

**Proposed:** Apply post-fusion adjustments:

- **Exact match boost:** If query appears in `retrieval_text`, boost score by 20%
- **Media type preference:** If user has historically clicked more images than videos, boost images by 10% (future: requires click tracking)
- **Quality signals:** Boost results with longer captions (proxy for richer content)

**Why:** Fusion alone cannot capture all relevance signals. Reranking adds domain-specific logic.

**How to apply:** Implement in `services/shared/semedia_shared/ranking_service.py:rerank_results()`.

#### 3.4 Diversity & Deduplication

**Current:** No diversity logic. Scenes from the same video can dominate results.

**Proposed:** Diversify results by parent media.

- After ranking, group results by `media_id`
- Select top N results, ensuring no more than 2 scenes from the same video in top 10
- If a video has multiple high-scoring scenes, show the best 2 and demote the rest

**Why:** Users want diverse results, not 8 scenes from the same video.

**How to apply:** Implement in `services/shared/semedia_shared/ranking_service.py:diversify_results()`.

### 4. Result Presentation Improvements

#### 4.1 Score Calibration

**Current:** Backend returns `score * 100`, frontend filters with `≥0.5`.

**Proposed:** Return scores in [0, 1] range and fix frontend filters.

- Backend: return `score` as float in [0, 1]
- Frontend: update score filters to `≥0.5`, `≥0.7`, `≥0.9` (now correct)
- Display scores as percentages in UI: `formatScore(score)` returns `${(score * 100).toFixed(0)}%`

**Why:** Current score handling is misleading. A score of 50 (out of 100) is filtered by `≥0.5`, which is nonsensical.

**How to apply:**
- Update `services/shared/semedia_shared/search_service.py:search_text()` to return `score` instead of `round(score * 100, 2)`
- Update `frontend/src/pages/SearchPage.tsx` score filter thresholds to `0.005`, `0.007`, `0.009` (since backend scores are now 0-1 but displayed as 0-100)
- Actually, better: keep backend scores as 0-1, update frontend to use `0.5`, `0.7`, `0.9` as thresholds, and update `formatScore()` to multiply by 100 for display

**Correction:** The cleanest approach:
- Backend returns scores in [0, 1]
- Frontend filters use [0, 1] thresholds: `0.5`, `0.7`, `0.9`
- Frontend displays scores as percentages: `${(score * 100).toFixed(0)}%`

#### 4.2 Component Scores & Explanations

**Current:** Only final score is returned.

**Proposed:** Return component scores and explanation labels.

```typescript
interface SearchResult {
  // ... existing fields
  score: number  // final score in [0, 1]
  vector_score: number  // CLIP similarity
  keyword_score: number  // TF-IDF similarity
  recency_score: number  // recency signal
  explanation: string  // e.g., "Strong visual match, exact keyword match"
}
```

**Why:** Users and developers need to understand why a result ranked high or low.

**How to apply:**
- Update `services/shared/semedia_shared/search_service.py:search_text()` to return component scores
- Add `services/shared/semedia_shared/explanation_service.py` to generate explanation strings
- Update `frontend/src/types/api.ts` and `frontend/src/components/SearchResultCard.tsx` to display explanations (optional, behind a "show details" toggle)

#### 4.3 Result Grouping

**Current:** Flat list of results.

**Proposed:** Group video scenes by parent media in UI.

- Backend returns results as flat list (unchanged)
- Frontend groups results by `media_id` and displays as expandable groups
- Show best scene from each video by default, with "Show N more scenes" button

**Why:** Improves UX when multiple scenes from the same video match.

**How to apply:** Update `frontend/src/pages/SearchPage.tsx` to group results by `media_id` before rendering.

#### 4.4 Sorting Fixes

**Current:** "Date" and "Size" sorting use filename string comparison.

**Proposed:** Use actual metadata.

- Add `created_at` and `file_size` to search results
- Frontend sorts by these fields instead of filename

**Why:** Current sorting is broken.

**How to apply:**
- Update `services/shared/semedia_shared/search_service.py:search_text()` to include `created_at` and `file_size` in results
- Update `frontend/src/pages/SearchPage.tsx` sorting logic

### 5. Evaluation Infrastructure

#### 5.1 Judged Query Set

**Proposed:** Build a test set of queries with judged relevance.

- Create `testing/evaluation/queries.json`:
  ```json
  [
    {
      "query": "cat on sofa",
      "relevant_media_ids": [1, 5],
      "relevant_scene_ids": [12, 13]
    }
  ]
  ```
- Manually judge 20-30 queries against current media library
- Store judgments in version control

**Why:** Without ground truth, we cannot measure improvement.

#### 5.2 Offline Metrics

**Proposed:** Compute retrieval metrics on judged query set.

- Precision@10
- Recall@10
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG@10)

**Implementation:**
- Add `testing/evaluation/evaluate_search.py` to compute metrics
- Run evaluation before and after changes to measure impact

#### 5.3 A/B Testing Hooks

**Proposed:** Add infrastructure for online A/B testing (future).

- Log search queries, results, and clicks to database
- Add `search_logs` table with `query`, `results`, `clicked_media_id`, `clicked_rank`
- Compute online metrics: click-through rate (CTR), mean reciprocal rank of clicked results

**Why:** Offline metrics are proxies. Online metrics measure real user satisfaction.

**How to apply:** Add logging in `services/search_api/app/main.py:search()`. Add analytics endpoint in `services/gateway_api/app/main.py`.

## Implementation Plan

### Phase 1: Indexing Improvements (Week 1)

**Goal:** Improve data quality for retrieval.

1. Add `retrieval_text` field to `MediaItem` and `VideoScene` models
2. Update `pipeline.py` to populate `retrieval_text` from caption + filename
3. Update `pipeline.py` to aggregate video-level caption from all scenes
4. Add multi-frame sampling to `video_service.py:extract_scene_keyframe()`
5. Update `pipeline.py` to process 3 frames per scene
6. Add adaptive scene detection threshold to `video_service.py:detect_scenes()`
7. Run migration and reprocess existing media

**Deliverables:**
- Database migration for new fields
- Updated processing pipeline
- Reprocessed media library

**Testing:**
- Verify 3 keyframes are extracted per scene
- Verify `retrieval_text` is populated
- Verify video-level caption is aggregated

### Phase 2: Retrieval Improvements (Week 2)

**Goal:** Stabilize and improve candidate generation.

1. Add `index_service.py` with TF-IDF index building and loading
2. Add `tfidf_doc_id` field to models
3. Update `pipeline.py` to trigger index rebuild on media changes
4. Update `search_api` startup to load TF-IDF index
5. Update `search_service.py` to use precomputed index instead of per-query fitting
6. Increase candidate pool size to `top_k * 5`
7. Add `query_service.py` with query preprocessing

**Deliverables:**
- Persistent TF-IDF index
- Faster keyword search
- Larger candidate pools

**Testing:**
- Verify index is built and loaded correctly
- Verify keyword search uses precomputed index
- Benchmark query latency (should improve)

### Phase 3: Ranking Improvements (Week 3)

**Goal:** Add reranking and diversity.

1. Add `ranking_service.py` with fusion, reranking, and diversity functions
2. Update `search_service.py` to call ranking pipeline
3. Add recency signal to fusion
4. Implement exact match boost in reranking
5. Implement diversity logic to limit scenes per video
6. Make fusion weights configurable via environment variables

**Deliverables:**
- Multi-stage ranking pipeline
- Configurable fusion weights
- Diversified results

**Testing:**
- Verify reranking boosts exact matches
- Verify diversity limits scenes per video
- Manually test search quality on sample queries

### Phase 4: Result Presentation (Week 4)

**Goal:** Fix UI score handling and add explanations.

1. Update `search_service.py` to return scores in [0, 1]
2. Update `search_service.py` to return component scores
3. Add `explanation_service.py` to generate explanation strings
4. Update frontend types and components to handle new fields
5. Fix frontend score filters to use [0, 1] thresholds
6. Add `created_at` and `file_size` to search results
7. Fix frontend sorting to use actual metadata
8. Add result grouping by `media_id` in frontend

**Deliverables:**
- Calibrated scores
- Component scores and explanations
- Fixed sorting
- Grouped results

**Testing:**
- Verify score filters work correctly
- Verify sorting uses actual metadata
- Verify result grouping displays correctly

### Phase 5: Evaluation Infrastructure (Week 5)

**Goal:** Build tools to measure search quality.

1. Create `testing/evaluation/queries.json` with 20-30 judged queries
2. Add `testing/evaluation/evaluate_search.py` to compute offline metrics
3. Run baseline evaluation on current system
4. Run evaluation after each phase to measure improvement
5. Add search logging infrastructure for future A/B testing

**Deliverables:**
- Judged query set
- Offline evaluation script
- Baseline metrics
- Search logging (optional)

**Testing:**
- Verify evaluation script computes metrics correctly
- Verify metrics improve after ranking changes

## Success Criteria

### Quantitative Metrics

- **Indexing:** 3 keyframes per scene, `retrieval_text` populated for all media
- **Retrieval:** TF-IDF index build time <10s for 1000 media items, query latency <500ms
- **Ranking:** Precision@10 improves by ≥20% on judged query set
- **Presentation:** Score filters work correctly, no UI bugs

### Qualitative Metrics

- Search results feel more relevant (manual testing)
- Video scenes are more diverse (no single video dominates)
- Scores and explanations are understandable

## Risks & Mitigations

### Risk: Reprocessing existing media is slow

**Mitigation:** Run reprocessing as background job. Add progress tracking. Allow incremental reprocessing.

### Risk: TF-IDF index becomes stale

**Mitigation:** Rebuild index on media add/delete. Add index version tracking. Add index rebuild endpoint for manual refresh.

### Risk: Multi-frame sampling increases storage and processing time

**Mitigation:** Start with 3 frames per scene (manageable). Monitor storage growth. Add frame count configuration.

### Risk: Ranking changes break existing user expectations

**Mitigation:** Deploy behind feature flag. Run A/B test. Collect user feedback.

### Risk: Evaluation set is too small or biased

**Mitigation:** Start with 20-30 queries, expand over time. Include diverse query types (objects, actions, scenes, text).

## Future Work

### Post-MVP Enhancements

- **LLM-based video summarization:** Replace scene caption aggregation with LLM-generated video summaries
- **OCR and object detection:** Add OCR text and detected objects to `retrieval_text`
- **Cross-encoder reranking:** Use a cross-encoder model to rerank top candidates
- **Query expansion:** Use LLM or word embeddings to expand queries
- **Personalization:** Use click history to personalize ranking
- **Federated search:** Search across multiple media libraries
- **Real-time indexing:** Update TF-IDF index incrementally instead of full rebuild

### Infrastructure Upgrades

- **Vector database:** Replace local cosine search with FAISS or Qdrant
- **Distributed processing:** Use Celery for async media processing
- **Caching:** Cache search results and embeddings
- **Monitoring:** Add search quality dashboards and alerts

## Appendix: File Changes Summary

### New Files

- `services/shared/semedia_shared/index_service.py` — TF-IDF index management
- `services/shared/semedia_shared/query_service.py` — Query preprocessing
- `services/shared/semedia_shared/ranking_service.py` — Multi-stage ranking pipeline
- `services/shared/semedia_shared/explanation_service.py` — Explanation generation
- `testing/evaluation/queries.json` — Judged query set
- `testing/evaluation/evaluate_search.py` — Offline evaluation script

### Modified Files

- `services/shared/semedia_shared/models.py` — Add `retrieval_text`, `tfidf_doc_id`, multi-frame fields
- `services/shared/semedia_shared/pipeline.py` — Update processing for new fields
- `services/shared/semedia_shared/video_service.py` — Multi-frame sampling, adaptive thresholds
- `services/shared/semedia_shared/search_service.py` — Use precomputed index, call ranking pipeline
- `services/shared/semedia_shared/config.py` — Add new configuration fields
- `services/search_api/app/main.py` — Load TF-IDF index at startup
- `frontend/src/types/api.ts` — Add new result fields
- `frontend/src/pages/SearchPage.tsx` — Fix score filters, add grouping, fix sorting
- `frontend/src/components/SearchResultCard.tsx` — Display component scores and explanations
- `frontend/src/utils/format.ts` — Update `formatScore()` for [0, 1] scores

### Database Migrations

- Add `retrieval_text` column to `media_items` and `video_scenes`
- Add `tfidf_doc_id` column to `media_items` and `video_scenes`
- Add `keyframe_paths`, `thumbnail_paths`, `captions`, `embeddings` columns to `video_scenes` (change from single to array)
- Add `best_frame_index` column to `video_scenes`

## Conclusion

This redesign transforms Semedia's search from a simplistic weighted sum into a proper multi-stage retrieval pipeline. By improving data processing, stabilizing retrieval, adding reranking and diversity, fixing result presentation, and building evaluation infrastructure, we address the systemic quality issues in the current implementation. The phased approach allows incremental delivery and validation, while the evaluation framework ensures future improvements are evidence-based.
