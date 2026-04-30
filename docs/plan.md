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
- Scene captions are generated once and used as both display text and retrieval text
- Video-level captioning is weak: the media caption is effectively derived from a single scene path
- Scene detection uses one fixed threshold for all video types
- No explicit retrieval text field exists for richer matching

### 2.2 Retrieval issues
- TF-IDF is rebuilt on every text query
- Keyword scoring changes with corpus shape at query time
- Candidate pools are too small before fusion
- No query preprocessing layer exists

### 2.3 Ranking issues
- Ranking is just normalized vector score + normalized keyword score with static weights
- No reranking rules exist
- No diversity logic prevents many scenes from one video dominating the result page
- No calibrated interpretation of backend scores exists

### 2.4 Frontend result-handling issues
- Backend returns scores scaled to 0-100
- Frontend score filters are written like 0.5 / 0.7 / 0.9, which mismatches backend semantics
- Client-side sorting for date and size is not based on actual metadata
- UI has no explanation of why a result matched

### 2.5 Evaluation gap
- Current tests verify API behavior, not retrieval quality
- No judged query set exists
- No offline metrics exist to compare algorithm revisions

## 3. Target System

The improved system will use a **multi-stage retrieval pipeline**:

1. **Processing and indexing**
   - Extract stronger scene and media representations
   - Store display text separately from retrieval text
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

## Phase 2 — Improve Processing and Indexing

### Goals
- Make indexed media representations more descriptive and stable
- Fix the upstream data weaknesses that reduce search quality

### Work

#### 2.1 Separate retrieval text from display caption
Add a new retrieval-oriented text field for both `MediaItem` and `VideoScene`.

Use cases:
- display caption remains concise
- retrieval text can include:
  - generated caption
  - sanitized filename tokens
  - parent media context
  - future OCR/object text

#### 2.2 Improve video-level aggregation
Replace the current weak video-level representation with a summary built from scene-level content.

MVP approach:
- aggregate scene captions into one video retrieval text field
- derive media caption from multiple scene summaries, not only one scene

#### 2.3 Improve scene representation
Replace one-keyframe-per-scene with multi-sample scene representation.

MVP approach:
- sample 3 frames per scene: early, middle, late
- generate captions/embeddings for all sampled frames
- choose the best-matching frame at retrieval time or aggregate them at indexing time

#### 2.4 Tune scene segmentation
Replace one fixed threshold with configurable logic based on video duration and scene density.

#### 2.5 Reprocess media
After indexing changes, reprocess the current library to rebuild captions, scene artifacts, and embeddings.

### Deliverables
- Updated schema for retrieval text and richer scene representation
- Updated processing pipeline
- Reprocessed corpus

### Success criteria
- Retrieval text exists for all completed images and scenes
- Video-level text is derived from more than one scene
- Scene representations are visibly more representative than midpoint-only snapshots

---

## Phase 3 — Build Durable Keyword Retrieval

### Goals
- Remove query-time TF-IDF rebuilding
- Make keyword search faster and more stable

### Work
1. Introduce a persistent keyword index service
2. Build TF-IDF index artifacts from retrieval text
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
- Rebuild flow after ingestion/reprocessing/deletion

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
- filename token boost where useful
- stronger confidence for richer retrieval text matches
- optional penalties for weak/noisy captions

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

---

## Phase 6 — Improve Result Presentation and UI Handling

### Goals
- Make search results clearer, more useful, and less misleading
- Align UI behavior with backend ranking semantics

### Work

#### 6.1 Fix score handling
- Align backend score range and frontend filters
- Update score display formatting

#### 6.2 Return richer ranking data
Extend API responses with:
- final score
- vector score
- keyword score
- optional rerank adjustments
- short explanation label

#### 6.3 Group related video scenes
Allow UI to show multiple strong scenes from the same video without flooding the page.

Possible presentation:
- best scene shown first
- related scenes expandable under the parent video

#### 6.4 Fix sort options
Replace filename-based sorting with real metadata fields:
- created time
- file size
- maybe media duration if useful

### Deliverables
- updated API response schema
- updated frontend types
- updated result card and search page behavior

### Success criteria
- UI filters behave correctly
- sorting behaves correctly
- users can understand why results appear

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

1. Build evaluation baseline first
2. Improve indexing and retrieval text
3. Add durable keyword index
4. Expand candidate generation
5. Add reranking and diversity
6. Fix API score semantics and frontend handling
7. Tune weights with evaluation loop
8. Reprocess corpus and run final regression pass

## 7. Risks and Mitigations

### Risk: reprocessing the media library is expensive
Mitigation:
- run as a staged background workflow
- support partial reprocessing
- measure processing time before full rollout

### Risk: richer scene representation increases storage
Mitigation:
- start with 3 frames per scene
- store thumbnails efficiently
- monitor storage growth before increasing sampling

### Risk: keyword index becomes stale
Mitigation:
- rebuild after ingestion, deletion, and reprocessing
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
- indexing uses richer retrieval text and better scene representation
- keyword search uses a durable prebuilt index
- ranking includes fusion, reranking, and diversity
- backend score semantics are clean and frontend filters match them
- results expose useful explanation and component-score information
- a judged query set and offline evaluation runner exist
- quality improves measurably against the baseline
- regression tests cover the new ranking pipeline behavior

## 9. Recommended Next Step

Start with **Phase 1: Audit and Baseline** and do not change ranking logic before the baseline dataset and metrics exist. This project is large enough that tuning without evaluation will create noise and make it difficult to know which changes actually help.
