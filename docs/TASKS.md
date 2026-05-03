# Search Quality Improvement - Implementation Tasks

**Project Start:** 2026-04-30  
**Status:** Phase 7 complete (locked benchmark, baseline report, metrics history, and tuning checklist complete; Phase 7 remains the accepted baseline)

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
- [x] 5.1 Create ranking service
  - [x] Create `services/shared/semedia_shared/ranking_service.py`
  - [x] Implement fusion layer (`rank_candidates()`)
  - [x] Implement reranking layer (exact phrase, filename token, rich caption boosts)
  - [x] Implement diversity layer (caption dedupe plus per-media cap)
- [x] 5.2 Implement fusion strategy
  - [x] Preserve configurable vector and keyword fusion weights from config
  - [x] Merge normalized vector and keyword candidates into a unified ranking pipeline
- [x] 5.3 Implement reranking rules
  - [x] Exact match boost (query phrase in caption)
  - [x] Filename token boost
  - [x] Quality signal boost (longer captions)
- [x] 5.4 Implement diversity logic
  - [x] Group results by `media_id`
  - [x] Limit scenes per video in top 10 (max 2)
  - [x] Deduplicate duplicate captions while preserving the top scene per video
- [x] 5.5 Implement score calibration
  - [x] Return scores in [0, 1] range
  - [x] Align frontend percentage formatting with normalized backend scores
- [x] 5.6 Integrate ranking pipeline into search
  - [x] Update `search_service.py:search_text()` to call ranking pipeline
  - [x] Update `search_service.py:search_image()` to call ranking pipeline
  - [x] Add ranking and search tests for reranking, diversity, and score normalization

**Success Criteria:**
- Better top-10 relevance on judged queries
- Less duplicate-heavy first page
- Scores become interpretable across result types

**Outcome:** Complete. Phase 5 introduced `ranking_service.py`, normalized search scores to `[0,1]`, added reranking and diversity controls, and improved live judged-query evaluation to Precision@10 0.1000, Recall@10 0.9444, MRR 0.6214, NDCG@10 0.6695. Full service tests and the smoke test passed.

---

## Phase 6 — Improve Result Presentation and UI Handling

**Goal:** Make search results clearer, more useful, and less misleading.

### Tasks
- [x] 6.1 Fix score handling
  - [x] Update backend to return scores in [0, 1] range
  - [x] Update frontend score filters to use [0, 1] thresholds with a permissive default (`0.0`, plus `0.5`, `0.7`, `0.9` options)
  - [x] Update `formatScore()` to display as percentages
  - [x] Rebuild frontend so the live bundle serves the fixed default filter
- [x] 6.2 Return richer ranking data
  - [x] Add `vector_score` to API response
  - [x] Add `keyword_score` to API response
  - [x] Add structured `explanation` field to API response
  - [x] Extend frontend `SearchResult` typing for richer ranking metadata
  - [x] Redesign `SearchResultCard` with badge-based ranking and explanation metadata
  - [x] Add detailed badge explanation panel to `SearchPage`
  - [x] Add backend and frontend tests covering richer ranking payloads and rendering
  - [x] Rebuild and verify the frontend stack
  - [x] Keep current implementation local to existing search and card components (no separate `explanation_service.py`)
- [x] 6.3 Group related video scenes
  - [x] Update frontend to group results by `media_id`
  - [x] Add expandable scene groups in UI
  - [x] Show best scene first with "Show N more scenes" button
- [x] 6.4 Fix sort options
  - [x] Add `created_at` to search results
  - [x] Add `file_size` to search results
  - [x] Update frontend sorting to use actual metadata
  - [x] Remove filename-based sorting

**Success Criteria:**
- ✅ UI filters behave correctly
- ✅ Sorting behaves correctly
- ✅ Users can understand why results appear

**Current status:**
- Score handling is complete and the live frontend now shows low-score text results by default.
- Richer ranking payloads, badge-based result cards, and the search-page explanation panel are complete.
- Grouped video-scene presentation is complete (2026-05-02).
- Real metadata-based sorting is complete (2026-05-02).

---

## Phase 7 — Evaluation Framework and Tuning Loop

**Goal:** Make search improvement iterative and measurable.

### Tasks
- [x] 7.1 Finalize judged dataset
  - [x] Add `testing/evaluation/asset_manifest.json`
  - [x] Commit 35+ locked local evaluation assets under `testing/evaluation/assets/`
  - [x] Expand `testing/evaluation/queries.json` to 100+ judged queries
  - [x] Double-check authenticity by comparing the actual media content against every judged query
  - [x] Add query categories
  - [x] Document judging criteria in query metadata and manual notes
- [x] 7.2 Build evaluation runner
  - [x] Enhance `testing/evaluation/evaluate_search.py`
  - [x] Add metric comparison reports
  - [x] Add regression detection
  - [x] Add modality, difficulty, and negative-query summaries
  - [x] Add CLI output saving and baseline comparison flow in `testing/evaluation/run_evaluation.py`
- [x] 7.3 Compute baseline vs new metrics
  - [x] Run Docker baseline evaluation against the locked corpus
  - [x] Save `testing/evaluation/baselines/baseline-phase7.json`
  - [x] Track improvements by query category
  - [x] Record the baseline in `docs/metrics/search_quality_history.md`
- [x] 7.4 Maintain metrics history and project tracking
  - [x] Create `docs/metrics/search_quality_history.md`
  - [x] Update `docs/plan.md` with Phase 7 deliverables
  - [x] Update `docs/TASKS.md` to reflect the locked benchmark workflow
- [x] 7.5 Create tuning checklist (`docs/metrics/search_tuning_checklist.md`)
  - [x] Document weight tuning process
  - [x] Document reranking rule tuning
  - [x] Document threshold tuning

**Success Criteria:**
- Every major ranking change is evaluated before adoption
- Relevance improvements are evidence-based
- Regression tests prevent quality degradation
- Locked local corpus, judged queries, and baseline workflow are documented in-project

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

- **Current Phase:** Phase 7 baseline remains current
- **Next Phase:** Revisit future retrieval experiments only if new measured evidence justifies them
- **Blocked Tasks:** None currently
- **Risks:** See `Semedia/docs/plan.md` section 7

## Progress Summary

- **Phase 1:** Complete (2026-04-30) — baseline metrics established and failure modes documented
- **Phase 2:** Complete (2026-04-30) — adaptive thresholds and batched inference implemented
- **Phase 3:** Complete (2026-04-30) — durable keyword retrieval implemented
- **Phase 4:** Complete (2026-04-30) — caption quality and cleanup refactor implemented
- **Phase 5:** Complete (2026-05-01) — ranking pipeline, normalized scores, reranking, and diversity implemented; live evaluation improved to Precision@10 0.1000, Recall@10 0.9444, MRR 0.6214, NDCG@10 0.6695
- **Phase 6:** Complete (2026-05-02)
  - 6.1 Complete — score handling and frontend filter alignment
  - 6.2 Complete — richer ranking data, badge-based result cards, search page explanation panel
  - 6.3 Complete — grouped video-scene presentation
  - 6.4 Complete — real metadata-based sorting
- **Phase 7:** Complete (2026-05-02) — locked benchmark corpus, judged dataset, baseline report, metrics history, and tuning checklist documented
- **Phase 8+:** Reverted / not active
