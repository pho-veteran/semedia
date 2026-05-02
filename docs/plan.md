# Search Quality Improvement Plan

**Date:** 2026-04-30
**Scope:** End-to-end improvement of Semedia search quality, from media processing and indexing through retrieval, ranking, reranking, diversity, and result presentation.

## 1. Objectives

We will improve search as a full retrieval system, not just tweak one ranking formula.

Primary goals:
- Improve the quality of indexed data so retrieval has stronger signals
- Improve candidate generation for both vector and keyword search
- Add a real ranking pipeline with reranking and diversity control
- Fix result presentation so scores, filters, and sorting are trustworthy
- Add an evaluation framework so improvements are measurable

Non-goals for this cycle:
- Moving to an external vector database
- Replacing the full architecture with new services
- Building heavy personalization or online learning

## 2. Current Problems

### 2.1 Processing and indexing issues
- Video scenes are represented by a single midpoint keyframe
- Scene captions are generated once and used as both display text and search text
- Video-level captioning aggregates from multiple scenes but could be richer
- Scene detection uses one fixed threshold for all video types
- Caption and embedding generation processes images one at a time instead of batching

### 2.2 Retrieval issues
- TF-IDF is rebuilt on every text query
- Keyword scoring changes with corpus shape at query time
- Keyword search uses only generated captions, not filenames or metadata
- Candidate pools are too small before fusion
- No query preprocessing layer exists

### 2.3 Ranking issues
- Ranking is just normalized vector score + normalized keyword score with static weights
- No reranking rules exist
- No diversity logic prevents many scenes from one video dominating the result page
- No calibrated interpretation of backend scores exists

### 2.4 Frontend result-handling issues
- Backend and frontend score semantics must stay aligned on a normalized `[0,1]` range
- Frontend score filters should continue to operate on the same `[0,1]` semantics used by the backend
- Client-side sorting for date and size is not based on actual metadata
- UI has no explanation of why a result matched

### 2.5 Evaluation gap
- Current tests verify API behavior, not retrieval quality
- No judged query set exists
- No offline metrics exist to compare algorithm revisions

## 3. Target System

The improved system will use a **multi-stage retrieval pipeline**:

1. **Processing and indexing**
   - Improve scene detection and processing throughput
   - Strengthen scene and media captions within the single-frame model
   - Build durable keyword index artifacts

2. **Candidate generation**
   - Retrieve a larger pool from vector search
   - Retrieve a larger pool from keyword search
   - Merge into a broader candidate set before ranking

3. **Ranking and reranking**
   - Fuse vector, keyword, and lightweight metadata signals
   - Apply reranking rules
   - Apply diversity controls to reduce duplicate-heavy pages

4. **Presentation**
   - Return calibrated scores
   - Return component signals and explanations
   - Support grouped video-scene presentation

5. **Evaluation**
   - Maintain a judged query set
   - Compute offline metrics for every algorithm revision

## 4. Implementation Phases

---

## Phase 1 — Audit and Baseline

### Goals
- Understand current retrieval behavior in detail
- Freeze a baseline before changing the algorithm
- Define how improvement will be measured

### Work
1. Inspect current pipeline outputs:
   - media captions
n   - scene captions
   - scene boundaries
   - scene thumbnail quality
   - stored embeddings
2. Collect representative search queries:
   - object-focused queries
   - action-focused queries
   - scene/context queries
   - broad vs precise queries
3. Create an evaluation dataset with judged relevance
4. Run baseline measurements
5. Document failure modes

### Deliverables
- `testing/evaluation/queries.json`
- Baseline metric report
- Failure-mode inventory

### Success criteria
- At least 20-30 judged queries
- Baseline Precision@10, Recall@10, MRR, NDCG@10 recorded
- Known ranking failures grouped into categories

---

## Phase 2 — Improve Processing Performance

### Goals
- Improve processing throughput without adding schema complexity
- Make scene detection adaptive to video characteristics
- Keep the single-frame scene model

### Work
1. Add adaptive scene detection thresholds based on video duration
2. Implement batched caption generation (8 images per batch)
3. Implement batched CLIP embedding inference (8 images per batch)

### Deliverables
- Adaptive scene detection in `video_service.py`
- Batched caption generation in `caption_service.py`
- Batched CLIP inference in `clip_service.py`

### Success criteria
- Short videos (<30s) use threshold 20.0
- Long videos (>10min) use threshold 35.0
- Caption and embedding generation process images in batches
- Processing throughput improved
- All tests pass

---

## Phase 3 — Build Durable Keyword Retrieval

### Goals
- Remove query-time TF-IDF rebuilding
- Make keyword search faster and more stable

### Work
1. Introduce a persistent keyword index service
2. Build TF-IDF index artifacts from caption text
3. Load keyword index at service startup
4. Rebuild keyword index when media changes
5. Associate stored documents with media/scene identifiers

### Proposed components
- `index_service.py`
- index build/load/search helpers
- versioned index artifact under storage or service-managed index directory

### Deliverables
- Persistent TF-IDF index
- Startup loading logic
- Rebuild flow after ingestion/deletion/library updates

### Success criteria
- No per-query full TF-IDF fit
- Consistent keyword retrieval behavior across repeated queries
- Lower text-query latency

---

## Phase 4 — Upgrade Candidate Generation

### Goals
- Give ranking enough candidates to work with
- Avoid early truncation errors

### Work
1. Increase vector candidate pool size
2. Increase keyword candidate pool size
3. Merge into a larger unified candidate set
4. Preserve component scores for downstream reranking

### Notes
- Final `top_k` should not control candidate-generation breadth directly
- Candidate set should be large enough to allow fusion + diversity without losing true positives too early

### Deliverables
- Candidate-generation parameters in config
- Unified candidate object containing vector and keyword components

### Success criteria
- More relevant items survive into reranking stage
- Tail-relevant matches no longer disappear too early

---

## Phase 5 — Add Ranking, Reranking, and Diversity

### Goals
- Replace single weighted fusion with a proper ranking pipeline
- Improve both precision and result-page quality

### Work

#### 5.1 Fusion layer
Combine normalized signals:
- vector similarity
- keyword similarity
- optional metadata signals such as recency or content completeness

#### 5.2 Reranking layer
Apply explicit rules after fusion:
- exact phrase boost
- stronger confidence for richer caption matches
- optional penalties for weak/noisy captions
- no filename-based ranking signal

#### 5.3 Diversity layer
Prevent result pages from being dominated by many scenes from one video.

Rules for MVP:
- limit the number of scenes from the same video in the first result page
- keep the highest-value scene first
- demote near-duplicate scenes

#### 5.4 Score calibration
Return scores in a clean range and define their semantics clearly.

Recommended decision:
- backend returns normalized scores in `[0, 1]`
- frontend formats them for display as percentages
- filters operate on the same `[0, 1]` range

### Deliverables
- `ranking_service.py`
- configurable ranking weights
- reranking rules
- diversity logic

### Success criteria
- Better top-10 relevance on judged queries
- Less duplicate-heavy first page
- Scores become interpretable across result types

### Status
- Complete
- Live judged-query evaluation improved to Precision@10 0.1000, Recall@10 0.9444, MRR 0.6214, NDCG@10 0.6695
- Full service tests and the smoke test passed

---

## Phase 6 — Improve Result Presentation and UI Handling

### Goals
- Make search results clearer, more useful, and less misleading
- Align UI behavior with backend ranking semantics

### Work

#### 6.1 Fix score handling
- Align backend score range and frontend filters
- Update score display formatting

#### 6.2 Return richer ranking data ✅
Extend API responses with:
- final score ✅
- vector score ✅
- keyword score ✅
- rerank adjustments ✅
- structured explanation object ✅

**Status:** Complete (2026-05-02)
- Backend exposes `vector_score`, `keyword_score`, and `explanation` in search payloads
- Frontend types extended with `SearchResultExplanation` interface
- Result cards redesigned with badge-based metadata layout
- Search page includes detailed explanation panel for badge meanings

#### 6.3 Group related video scenes ✅
Allow UI to show multiple strong scenes from the same video without flooding the page.

**Status:** Complete (2026-05-02)
- Frontend groups results by `media_id` using `buildSearchRenderEntries()` utility
- `SearchResultGroup` component renders lead scene with expandable preview strip
- Best scene shown first, up to 2 preview scenes visible, remaining scenes behind "Show N more" button
- Keyboard navigation preserved across top-level render entries only

#### 6.4 Fix sort options ✅
Replace filename-based sorting with real metadata fields.

**Status:** Complete (2026-05-02)
- Backend search results now include `created_at` (from `uploaded_at`) and `file_size`
- Frontend `SearchResult` type extended with `file_size: number` and `created_at: string`
- Date sort uses `created_at` timestamp (newest first)
- Size sort uses `file_size` bytes (largest first)
- Filename-based sorting removed

### Deliverables
- ✅ updated API response schema
- ✅ updated frontend types
- ✅ updated result card and search page behavior
- ✅ grouped video-scene presentation
- ✅ real metadata-based sorting

### Success criteria
- ✅ UI filters behave correctly
- ✅ users can understand why results appear
- ✅ sorting behaves correctly

---

## Phase 7 — Evaluation Framework and Tuning Loop

### Goals
- Make search improvement iterative and measurable
- Prevent future regressions

### Work
1. Finalize judged dataset
2. Build evaluation runner
3. Compute baseline vs new metrics after every major algorithm revision
4. Track improvements by query category
5. Add optional query/result logging hooks for future online evaluation

### Metrics
- Precision@10
- Recall@10
- MRR
- NDCG@10
- qualitative failure counts by category

### Deliverables
- `testing/evaluation/evaluate_search.py`
- reproducible metric reports
- tuning checklist for weights and rules

### Success criteria
- Every major ranking change is evaluated before adoption
- Relevance improvements are evidence-based, not subjective only

---

## 5. File-Level Change Plan

### Backend shared package
Likely changes in:
- `services/shared/semedia_shared/models.py`
- `services/shared/semedia_shared/pipeline.py`
- `services/shared/semedia_shared/video_service.py`
- `services/shared/semedia_shared/caption_service.py`
- `services/shared/semedia_shared/clip_service.py`
- `services/shared/semedia_shared/search_service.py`
- `services/shared/semedia_shared/config.py`

### New backend modules
Add:
- `services/shared/semedia_shared/index_service.py`
- `services/shared/semedia_shared/query_service.py`
- `services/shared/semedia_shared/ranking_service.py`
- optional `services/shared/semedia_shared/explanation_service.py`

### Search API
Likely changes in:
- `services/search_api/app/main.py`

### Frontend
Likely changes in:
- `frontend/src/pages/SearchPage.tsx`
- `frontend/src/components/SearchResultCard.tsx`
- `frontend/src/types/api.ts`
- `frontend/src/utils/format.ts`

### Testing
Add/update:
- `testing/services/test_search_api.py`
- `testing/evaluation/queries.json`
- `testing/evaluation/evaluate_search.py`

## 6. Recommended Execution Order

1. ✅ Improve processing throughput and scene detection (Phase 2 complete)
2. ✅ Build evaluation baseline (Phase 1 complete)
3. ✅ Add durable keyword index (Phase 3 complete)
4. ✅ Improve caption quality (Phase 4 complete)
5. ✅ Add reranking and diversity (Phase 5 complete)
6. ✅ Fix API score semantics and frontend handling baseline (Phase 6.1 complete)
7. Add richer ranking data, scene grouping, and real metadata sorting (remaining Phase 6)
8. Expand candidate generation (Phase 8)
9. Tune weights with evaluation loop (Phase 7)
10. Run final regression pass

## 7. Risks and Mitigations

### Risk: processing throughput is still too slow on large libraries
Mitigation:
- keep batched caption and embedding inference
- measure processing time after each change
- tune batch size before larger architectural changes

### Risk: adaptive scene thresholds still miss some scene boundaries
Mitigation:
- compare scene splits across short and long videos
- tune duration-based thresholds using real samples
- keep threshold logic simple until evaluation data suggests otherwise

### Risk: keyword index becomes stale
Mitigation:
- rebuild after ingestion, deletion, and library updates
- track index version
- add manual rebuild command

### Risk: ranking gets more complex but not better
Mitigation:
- require offline evaluation before keeping changes
- tune one layer at a time
- preserve baseline metrics for rollback comparison

### Risk: UI changes obscure backend relevance issues
Mitigation:
- separate backend ranking validation from frontend UX changes
- verify API ranking first, then visual grouping and filters

## 8. Definition of Done

This improvement cycle is done when:
- scene detection uses adaptive thresholds based on video duration
- caption and embedding generation use batched inference
- keyword search uses a durable prebuilt index
- ranking includes fusion, reranking, and diversity
- backend score semantics are clean and frontend filters match them
- results expose useful explanation and component-score information
- a judged query set and offline evaluation runner exist
- quality improves measurably against the baseline
- regression tests cover the new ranking pipeline behavior

## 9. Recommended Next Step

Phases 1 through 5 are complete, and Phase 6.1 and 6.2 are complete. The remaining Phase 6 work is **scene grouping (6.3)** and **real metadata-based sorting (6.4)**.

The main remaining issues are grouped video-scene presentation and metadata-based sorting. The best next move is to ship the remaining Phase 6 UI work, then revisit candidate generation (Phase 8) or caption vocabulary (Phase 10) only if judged-query metrics plateau again.
