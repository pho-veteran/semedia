# Search Quality Improvement - Implementation Tasks

**Project Start:** 2026-04-30  
**Status:** Phase 2 complete / Phase 3 ready

## Phase 1 — Audit and Baseline

**Goal:** Understand current retrieval behavior and establish baseline metrics before making changes.

### Tasks
- [x] 1.1 Inspect current pipeline outputs
  - [x] Review media captions quality
  - [x] Review scene captions quality
  - [x] Review scene boundaries and segmentation
  - [x] Review scene thumbnail quality
  - [x] Inspect stored embeddings
- [x] 1.2 Collect representative search queries
  - [x] Object-focused queries (e.g., "cat", "car", "person")
  - [x] Action-focused queries (e.g., "running", "cooking", "dancing")
  - [x] Scene/context queries (e.g., "sunset", "office", "beach")
  - [x] Broad vs precise queries
- [x] 1.3 Create evaluation dataset with judged relevance
  - [x] Create `testing/evaluation/queries.json` structure
  - [x] Manually judge 20-30 queries against current media library
- [x] 1.4 Run baseline measurements
  - [x] Implement evaluation script (`testing/evaluation/evaluate_search.py`)
  - [x] Compute Precision@10
  - [x] Compute Recall@10
  - [x] Compute MRR
  - [x] Compute NDCG@10
- [x] 1.5 Document failure modes
  - [x] Categorize ranking failures
  - [x] Document weak scene representations
  - [x] Document keyword search instability issues

**Success Criteria:**
- At least 20-30 judged queries in `testing/evaluation/queries.json`
- Baseline metrics recorded (Precision@10, Recall@10, MRR, NDCG@10)
- Known ranking failures grouped into categories

---

## Phase 2 — Improve Processing Performance

**Goal:** Improve processing throughput and scene detection quality without adding schema complexity.

### Tasks
- [x] 2.1 Add adaptive scene detection thresholds
  - [x] Update `video_service.py:detect_scenes()` with adaptive threshold logic
  - [x] Add duration-based threshold adjustment (<30s: 20.0, >10min: 35.0)
- [x] 2.2 Add batched caption generation
  - [x] Update `caption_service.py:generate_captions()` to batch process images
  - [x] Add chunking (8 images per batch) to prevent memory spikes
  - [x] Preserve fallback behavior
- [x] 2.3 Add batched CLIP embedding inference
  - [x] Update `clip_service.py:encode_images()` to batch process images
  - [x] Add chunking (8 images per batch) to prevent memory spikes
  - [x] Preserve fallback behavior

**Success Criteria:**
- Adaptive scene detection thresholds based on video duration
- Batched caption generation (8 images per batch)
- Batched CLIP embedding inference (8 images per batch)
- Processing throughput improved
- All tests pass

---

## Phase 3 — Build Durable Keyword Retrieval

**Goal:** Remove query-time TF-IDF rebuilding and stabilize keyword search.

### Tasks
- [ ] 3.1 Create persistent keyword index service
  - [ ] Create `services/shared/semedia_shared/index_service.py`
  - [ ] Implement `build_tfidf_index()` function
  - [ ] Implement `load_tfidf_index()` function
  - [ ] Implement `search_tfidf_index()` function
- [ ] 3.2 Add index tracking to models
  - [ ] Add `tfidf_doc_id` field to `MediaItem` model
  - [ ] Add `tfidf_doc_id` field to `VideoScene` model
  - [ ] Create database migration
- [ ] 3.3 Integrate index building into pipeline
  - [ ] Update `pipeline.py` to trigger index rebuild on media add
  - [ ] Add index rebuild on media delete
  - [ ] Add index rebuild on reprocessing
- [ ] 3.4 Load index at service startup
  - [ ] Update `services/search_api/app/main.py:lifespan()` to load TF-IDF index
  - [ ] Add error handling for missing index
- [ ] 3.5 Update search service to use precomputed index
  - [ ] Update `search_service.py:_keyword_results()` to use precomputed index
  - [ ] Remove per-query TF-IDF fitting logic

**Success Criteria:**
- No per-query TF-IDF fit
- Consistent keyword retrieval behavior across repeated queries
- Lower text-query latency

---

## Phase 4 — Upgrade Candidate Generation

**Goal:** Give ranking enough candidates to work with.

### Tasks
- [ ] 4.1 Increase candidate pool sizes
  - [ ] Update `search_service.py:_vector_results()` to return `top_k * 5`
  - [ ] Update `search_service.py:_keyword_results()` to return `top_k * 5`
- [ ] 4.2 Add candidate-generation configuration
  - [ ] Add `SEARCH_CANDIDATE_MULTIPLIER` to config
  - [ ] Update search service to use configurable multiplier
- [ ] 4.3 Preserve component scores
  - [ ] Update candidate objects to store vector and keyword scores separately
  - [ ] Pass component scores through to ranking pipeline

**Success Criteria:**
- More relevant items survive into reranking stage
- Tail-relevant matches no longer disappear too early

---

## Phase 5 — Add Ranking, Reranking, and Diversity

**Goal:** Replace single weighted fusion with a proper ranking pipeline.

### Tasks
- [ ] 5.1 Create ranking service
  - [ ] Create `services/shared/semedia_shared/ranking_service.py`
  - [ ] Implement fusion layer (`rank_candidates()`)
  - [ ] Implement reranking layer (`rerank_results()`)
  - [ ] Implement diversity layer (`diversify_results()`)
- [ ] 5.2 Implement fusion strategy
  - [ ] Add recency score calculation
  - [ ] Add configurable fusion weights to config
  - [ ] Implement weighted fusion: `w_vector * vector + w_keyword * keyword + w_recency * recency`
- [ ] 5.3 Implement reranking rules
  - [ ] Exact match boost (query in `retrieval_text`)
  - [ ] Quality signal boost (longer captions)
  - [ ] Filename token boost
- [ ] 5.4 Implement diversity logic
  - [ ] Group results by `media_id`
  - [ ] Limit scenes per video in top 10 (max 2)
  - [ ] Demote near-duplicate scenes
- [ ] 5.5 Implement score calibration
  - [ ] Return scores in [0, 1] range
  - [ ] Define score semantics clearly
- [ ] 5.6 Integrate ranking pipeline into search
  - [ ] Update `search_service.py:search_text()` to call ranking pipeline
  - [ ] Update `search_service.py:search_image()` to call ranking pipeline

**Success Criteria:**
- Better top-10 relevance on judged queries
- Less duplicate-heavy first page
- Scores become interpretable across result types

---

## Phase 6 — Improve Result Presentation and UI Handling

**Goal:** Make search results clearer, more useful, and less misleading.

### Tasks
- [ ] 6.1 Fix score handling
  - [ ] Update backend to return scores in [0, 1] range
  - [ ] Update frontend score filters to use [0, 1] thresholds (0.5, 0.7, 0.9)
  - [ ] Update `formatScore()` to display as percentages
- [ ] 6.2 Return richer ranking data
  - [ ] Add `vector_score` to API response
  - [ ] Add `keyword_score` to API response
  - [ ] Add `recency_score` to API response
  - [ ] Add `explanation` field to API response
  - [ ] Create `services/shared/semedia_shared/explanation_service.py`
- [ ] 6.3 Group related video scenes
  - [ ] Update frontend to group results by `media_id`
  - [ ] Add expandable scene groups in UI
  - [ ] Show best scene first with "Show N more scenes" button
- [ ] 6.4 Fix sort options
  - [ ] Add `created_at` to search results
  - [ ] Add `file_size` to search results
  - [ ] Update frontend sorting to use actual metadata
  - [ ] Remove filename-based sorting

**Success Criteria:**
- UI filters behave correctly
- Sorting behaves correctly
- Users can understand why results appear

---

## Phase 7 — Evaluation Framework and Tuning Loop

**Goal:** Make search improvement iterative and measurable.

### Tasks
- [ ] 7.1 Finalize judged dataset
  - [ ] Expand query set if needed
  - [ ] Add query categories
  - [ ] Document judging criteria
- [ ] 7.2 Build evaluation runner
  - [ ] Enhance `testing/evaluation/evaluate_search.py`
  - [ ] Add metric comparison reports
  - [ ] Add regression detection
- [ ] 7.3 Compute baseline vs new metrics
  - [ ] Run evaluation after each major change
  - [ ] Track improvements by query category
  - [ ] Document metric changes
- [ ] 7.4 Add query/result logging hooks
  - [ ] Add `search_logs` table
  - [ ] Log queries, results, and clicks
  - [ ] Add analytics endpoint
- [ ] 7.5 Create tuning checklist
  - [ ] Document weight tuning process
  - [ ] Document reranking rule tuning
  - [ ] Document threshold tuning

**Success Criteria:**
- Every major ranking change is evaluated before adoption
- Relevance improvements are evidence-based
- Regression tests prevent quality degradation

---

## Notes

- **Current Phase:** Phase 2 (Improve Processing Performance)
- **Next Phase:** Phase 3 (Build Durable Keyword Retrieval)
- **Blocked Tasks:** None yet
- **Risks:** See `Semedia/docs/plan.md` section 7

## Progress Summary

- **Phase 1:** Complete (2026-04-30) — baseline metrics: all 0.0 due to poor caption quality
- **Phase 2:** Complete (2026-04-30) — adaptive thresholds and batched inference implemented
- **Phase 3:** Not started
- **Phase 4:** Not started
- **Phase 5:** Not started
- **Phase 6:** Not started
- **Phase 7:** Not started
