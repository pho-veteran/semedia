# Search Quality Redesign

**Date:** 2026-04-30  
**Status:** Partially implemented — Phases 1-4 complete, Phases 5+ remain as future work

## Implementation Status (as of 2026-05-01)

**✅ Completed:**
- **Phase 1 (Evaluation baseline):** Judged query set created, evaluation script implemented, baseline metrics recorded (all 0.0 due to poor caption quality)
- **Phase 2 (Processing performance):** Adaptive scene detection thresholds implemented, batched caption and CLIP inference added
- **Phase 3 (Durable keyword retrieval):** Persistent TF-IDF index implemented as database-backed artifacts, per-query rebuilding eliminated, keyword search stabilized
- **Phase 4 (Caption quality):** Caption cleanup refactored and extracted to `caption_cleanup_config.py`, weak-caption policy relaxed to preserve awkward but useful captions, live evaluation improved to Precision@10 0.0889, Recall@10 0.8333, MRR 0.5262, NDCG@10 0.5692

**❌ Not implemented (superseded or deferred):**
- Multi-frame scene sampling (section 1.1) — **superseded by single-frame model with improved caption quality**
- Retrieval text field (section 1.2) — **deferred; caption-only retrieval proved sufficient after Phase 4**
- Video-level caption aggregation (section 1.3) — **deferred; current first-scene approach acceptable for MVP**
- Larger candidate pools (section 2.2) — **deferred until ranking pipeline exists**
- Query preprocessing (section 2.3) — **deferred; not yet a bottleneck**
- Multi-stage ranking pipeline (section 3) — **next priority (Phase 5)**
- Result presentation fixes (section 4) — **deferred until ranking is in place**
- A/B testing hooks (section 5.3) — **future work**

**Current bottleneck:** Ranking quality and missing semantic coverage for hard queries, not caption structure or weak-caption strictness.

**Recommended next step:** Implement Phase 5 (ranking, reranking, and diversity) to improve top-result quality now that keyword retrieval is durable and caption cleanup has improved text signals.

---

## Executive Summary

This document specifies a comprehensive redesign of Semedia's search and ranking system to address systemic quality issues in data processing, retrieval, ranking, and result presentation. The original design proposed multi-frame scene sampling, retrieval-text enrichment, and a full ranking pipeline. Implementation proceeded incrementally, prioritizing durable keyword retrieval and caption quality first. The current system uses single-frame scenes with improved captions, durable TF-IDF indexing, and simple weighted fusion. The remaining work focuses on ranking improvements and result presentation.

---

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

## Remaining Roadmap

### Phase 5 — Ranking Improvements

**Goal:** Add reranking and diversity.

1. Add `ranking_service.py` with fusion, reranking, and diversity functions
2. Update `search_service.py` to call the ranking pipeline
3. Add recency signal to fusion if it improves measured relevance
4. Implement reranking rules for exact match and caption quality
5. Implement diversity logic to limit scenes per video
6. Make fusion weights configurable via environment variables

**Deliverables:**
- Multi-stage ranking pipeline
- Configurable fusion weights
- Diversified results

**Testing:**
- Verify reranking boosts exact matches
- Verify diversity limits scenes per video
- Re-run judged-query evaluation after each ranking change

### Phase 6 — Result Presentation

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

### Phase 7 — Evaluation Infrastructure Enhancements

**Goal:** Improve measurement and regression detection.

1. Expand the judged query set if needed
2. Add metric comparison reports and regression detection
3. Track improvements by query category
4. Add optional search logging infrastructure for future A/B testing

**Deliverables:**
- Improved evaluation runner
- Metric comparison reports
- Optional search logging hooks

**Testing:**
- Verify evaluation reports stay reproducible
- Verify regressions are surfaced clearly
- Keep quality changes evidence-based

### Longer-Term Work

- Revisit candidate pool expansion once ranking exists
- Consider stronger caption models or light semantic enrichment for hard queries
- Consider OCR, object detection, or richer media understanding only if measured gains justify the complexity
- Consider infrastructure upgrades such as vector indexes or external search components only if scale requires them

---

## Success Criteria

### Quantitative Metrics

- **Retrieval:** TF-IDF index build time remains reasonable for the current corpus, query-time TF-IDF fitting stays eliminated
- **Ranking:** Precision@10 improves materially on the judged query set
- **Presentation:** Score filters work correctly, sorting uses real metadata, UI behavior matches backend semantics

### Qualitative Metrics

- Search results feel more relevant in manual checks
- Video scenes are more diverse on the first page
- Scores and explanations are understandable
- Hard queries no longer fail mainly because of ranking order alone

## Risks & Mitigations

### Risk: Reprocessing existing media is slow

**Mitigation:** Keep reprocessing as a controlled batch step. Use the evaluation set to justify reruns.

### Risk: TF-IDF index becomes stale

**Mitigation:** Keep rebuilds after processing and deletion. Preserve artifact versioning and manual rebuild options.

### Risk: Ranking changes add complexity without improving relevance

**Mitigation:** Re-run judged-query evaluation after each major ranking change and keep changes incremental.

### Risk: Evaluation set is too small or biased

**Mitigation:** Expand the query set only when current metrics stop discriminating changes clearly.

## Appendix: File Changes Summary

### Implemented files so far

- `services/shared/semedia_shared/index_service.py` — durable TF-IDF index management
- `services/shared/semedia_shared/caption_cleanup_config.py` — extracted caption cleanup policy
- `testing/evaluation/queries.json` — judged query set
- `testing/evaluation/evaluate_search.py` — offline evaluation script

### Future files likely to change

- `services/shared/semedia_shared/ranking_service.py` — future multi-stage ranking pipeline
- `services/shared/semedia_shared/explanation_service.py` — future explanation generation
- `frontend/src/types/api.ts` — future result-field updates
- `frontend/src/pages/SearchPage.tsx` — future score, sort, and grouping updates
- `frontend/src/components/SearchResultCard.tsx` — future explanation display

## Conclusion

This redesign started as a broad search-system overhaul. In implementation, the highest-value early wins came from stabilizing keyword retrieval and improving caption quality while keeping the simpler single-frame scene model. The remaining roadmap now centers on ranking quality, result presentation, and evaluation-driven iteration rather than revisiting the caption cleanup refactor or reintroducing superseded multi-frame plans.

---

## Historical Note

This file is preserved as the original redesign spec, but some proposed sections were superseded during implementation. For the active execution status and next steps, prefer `docs/TASKS.md`, `docs/plan.md`, and the implementation notes under `docs/implementations/`.
