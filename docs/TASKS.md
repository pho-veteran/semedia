# Search Quality Improvement - Implementation Tasks

**Project Start:** 2026-04-30  
**Status:** Phase 4 complete / Phase 5 ready

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
- [x] 3.1 Create persistent keyword index service
  - [x] Create `services/shared/semedia_shared/index_service.py`
  - [x] Implement index build, load, persist, and search helpers
  - [x] Store durable keyword index artifacts in the database
- [x] 3.2 Add index tracking to models
  - [x] Add `KeywordIndexArtifact` model
  - [x] Persist serialized TF-IDF artifact payloads with versioning metadata
  - [x] Ensure schema creation covers the new artifact table
- [x] 3.3 Integrate index building into pipeline
  - [x] Update `pipeline.py` to trigger index rebuild after successful processing
  - [x] Add index rebuild on media delete
  - [x] Support rebuild on reprocessing through normal processing flow
- [x] 3.4 Load index at service startup
  - [x] Update `services/search_api/app/main.py:lifespan()` to load keyword index
  - [x] Handle missing or empty index artifacts safely
- [x] 3.5 Update search service to use precomputed index
  - [x] Update `search_service.py:_keyword_results()` to use precomputed index
  - [x] Remove per-query TF-IDF fitting logic
- [x] 3.6 Verify durable keyword retrieval behavior
  - [x] Add service tests for artifact creation and rebuild behavior
  - [x] Confirm repeated queries use stable keyword retrieval behavior

**Success Criteria:**
- No per-query TF-IDF fit
- Consistent keyword retrieval behavior across repeated queries
- Lower text-query latency
- Durable keyword index loads on search-api startup
- Keyword index rebuilds after media processing and deletion

**Outcome:** Complete. Durable keyword retrieval is implemented and wired through the shared search stack.
---

## Phase 4 — Improve Caption Quality

**Goal:** Improve caption quality and preserve slightly awkward but useful captions so retrieval has better text signals.

### Tasks
- [x] 4.1 Tune caption generation behavior
  - [x] Use stronger generation parameters for initial captioning
  - [x] Add stricter retry generation settings for weak captions
  - [x] Keep batched inference from Phase 2
- [x] 4.2 Add caption cleanup and normalization
  - [x] Normalize whitespace and punctuation
  - [x] Strip malformed tokens and verbose boilerplate phrases
  - [x] Preserve useful searchable text instead of over-cleaning
- [x] 4.3 Relax weak-caption filtering
  - [x] Reject truly generic captions
  - [x] Accept awkward but retrieval-useful captions from the low-capability model
  - [x] Keep fallback caption only for genuinely weak outputs
- [x] 4.4 Refactor cleanup configuration
  - [x] Extract cleanup constants into `services/shared/semedia_shared/caption_cleanup_config.py`
  - [x] Simplify `caption_service.py` by removing alias-heavy cleanup definitions
- [x] 4.5 Validate caption-quality behavior
  - [x] Update `testing/services/test_caption_service.py` for relaxed policy coverage
  - [x] Keep pipeline quality tests passing
  - [x] Reprocess the corpus and rerun live evaluation

**Success Criteria:**
- Generic captions are reduced without discarding useful awkward captions
- Caption cleanup rules are centralized and maintainable
- Search quality metrics move off the zero baseline
- Live evaluation shows improved retrieval behavior

**Outcome:** Complete. Caption cleanup was extracted and refactored, the relaxed weak-caption policy was applied, and live evaluation improved to Precision@10 0.0889, Recall@10 0.8333, MRR 0.5262, NDCG@10 0.5692.

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
  - [ ] Exact match boost (query in retrieval text or equivalent search text)
  - [ ] Quality signal boost (longer captions)
  - [ ] Diversity-aware penalties for duplicate-heavy results
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

## Phase 8 — Expand Candidate Generation

**Goal:** Give ranking enough candidates to work with.

### Tasks
- [ ] 8.1 Increase candidate pool sizes
  - [ ] Update `search_service.py:_vector_results()` to return a larger candidate pool
  - [ ] Update `search_service.py:_keyword_results()` to return a larger candidate pool
- [ ] 8.2 Add candidate-generation configuration
  - [ ] Add configurable candidate multiplier to search settings
  - [ ] Update search service to use configurable multiplier
- [ ] 8.3 Preserve component scores
  - [ ] Update candidate objects to store vector and keyword scores separately
  - [ ] Pass component scores through to ranking pipeline

**Success Criteria:**
- More relevant items survive into reranking stage
- Tail-relevant matches no longer disappear too early
- Ranking has enough candidates to recover from early retrieval misses

---

## Phase 9 — Future Evaluation and Logging Enhancements

**Goal:** Extend observability and tuning once the main ranking pipeline is in place.

### Tasks
- [ ] 9.1 Add query/result logging hooks
  - [ ] Add `search_logs` table
  - [ ] Log queries, results, and clicks
  - [ ] Add analytics endpoint
- [ ] 9.2 Create tuning checklist
  - [ ] Document weight tuning process
  - [ ] Document reranking rule tuning
  - [ ] Document threshold tuning

**Success Criteria:**
- Search changes are easier to tune with real usage data
- Regression detection can incorporate logged behavior
- Future relevance work is easier to measure and audit

---

## Phase 10 — Longer-Term Retrieval Enhancements

**Goal:** Address remaining retrieval gaps once ranking and presentation are in place.

### Tasks
- [ ] 10.1 Improve caption semantic coverage
  - [ ] Explore richer caption models or second-pass caption refinement
  - [ ] Consider light synonym or scene-term enrichment where justified
- [ ] 10.2 Improve query preprocessing
  - [ ] Normalize and expand hard queries carefully
  - [ ] Evaluate any preprocessing against the judged dataset
- [ ] 10.3 Revisit retrieval-text enrichment
  - [ ] Add new text signals only if they improve measured relevance without masking caption quality issues

**Success Criteria:**
- Hard queries like `mountain landscape`, `water`, and `night scene` gain better textual support
- Improvements are measurable on the judged dataset
- Retrieval quality increases without relying on misleading shortcuts

---

## Phase 11 — Optional Product and Infrastructure Follow-Ups

**Goal:** Capture larger future opportunities beyond the current search-quality cycle.

### Tasks
- [ ] 11.1 Consider stronger retrieval infrastructure
  - [ ] Evaluate local vector index improvements or external vector stores if scale requires it
- [ ] 11.2 Consider richer media understanding
  - [ ] OCR, object detection, or stronger video summarization
- [ ] 11.3 Consider search UX enhancements
  - [ ] Additional explanations, grouping controls, or analytics-driven tuning

**Success Criteria:**
- Future opportunities are clear without blocking the current ranking roadmap
- Larger architectural changes remain optional and evidence-driven

---

## Notes

- **Current Phase:** Phase 4 complete
- **Next Phase:** Phase 5 (Add Ranking, Reranking, and Diversity)
- **Blocked Tasks:** None currently
- **Risks:** See `Semedia/docs/plan.md` section 7

## Progress Summary

- **Phase 1:** Complete (2026-04-30) — baseline metrics established and failure modes documented
- **Phase 2:** Complete (2026-04-30) — adaptive thresholds and batched inference implemented
- **Phase 3:** Complete (2026-04-30) — durable keyword retrieval implemented
- **Phase 4:** Complete (2026-04-30) — caption quality and cleanup refactor implemented
- **Phase 5:** Not started
- **Phase 6:** Not started
- **Phase 7:** Not started
- **Phase 8+:** Not started
