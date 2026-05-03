# Phase 7 — Evaluation Benchmark and Metrics Tracking

**Date:** 2026-05-02  
**Status:** Approved design  
**Scope:** Build a large, locked, local evaluation benchmark for search quality with reproducible metric tracking and algorithm change history.

## 1. Objectives

Phase 7 will establish a **large-scale evaluation framework** for Semedia search quality that is:
- **Reproducible** — locked local assets with no runtime internet dependency
- **Comprehensive** — balanced coverage across objects, actions, scenes, negatives, and near-misses
- **Traceable** — structured reports plus human-readable history of algorithm changes and metric movements
- **Regression-safe** — automated comparison against saved baselines

### Primary goals
- Build a large locked benchmark corpus of local media assets
- Expand the judged query set to 100+ queries with balanced coverage
- Strictly verify dataset authenticity by manually comparing the actual media content against the judged queries
- Extend evaluation tooling for richer reporting and baseline comparison
- Run and document a baseline evaluation for the locked corpus
- Add metrics history documentation to track algorithm changes over time
- Broaden test coverage for evaluation infrastructure

### Non-goals for this phase
- No media download/fetch tooling
- No live internet dependency in evaluation runs
- No production search logging hooks
- No new retrieval or ranking algorithm changes
- No replacement of smoke tests (this is a separate evaluation layer)

## 2. Current State

### Existing evaluation infrastructure
- `testing/evaluation/evaluate_search.py` — core metric computation (Precision@10, Recall@10, MRR, NDCG@10)
- `testing/evaluation/queries.json` — small judged query set (20 queries)
- `testing/evaluation/seed_media.py` — uploads smoke assets for evaluation
- `testing/smoke-assets/` — 12 small test files used for stack validation

### Current limitations
- Query set is too small for reliable metric discrimination
- Smoke assets are tiny and partly misleading (e.g., `cat.jpg` depicts dogs)
- No separation between stack-validation fixtures and search-quality benchmarks
- No baseline comparison or regression detection
- No metrics history tracking
- Limited test coverage for evaluation infrastructure
- No asset metadata or provenance tracking

## 3. Target System

### 3.1 Corpus Structure

**New locked evaluation asset area**
- Location: `testing/evaluation/assets/`
- Purpose: search-quality benchmark, separate from smoke-test fixtures
- Size: **35+ assets minimum**
- Mix: **~80% images, ~20% videos**
- Stability: fixed once committed; metric changes reflect algorithm changes, not dataset drift

**Asset manifest**
- Location: `testing/evaluation/asset_manifest.json`
- Purpose: per-asset metadata for auditability and maintenance
- Fields per asset:
  - `asset_id` — stable identifier
  - `filename` — actual file in `assets/`
  - `media_type` — `image` or `video`
  - `categories` — content tags (e.g., `["outdoor", "vehicle", "daytime"]`)
  - `description` — brief content summary
  - `source` — provenance note (e.g., "public domain", "CC0", "project-created")
  - `notes` — optional maintenance notes

**Separation from smoke assets**
- `testing/smoke-assets/` remains for stack validation and smoke tests
- `testing/evaluation/assets/` is for search-quality evaluation only
- No overlap or reuse between the two sets

### 3.2 Judgments and Query Coverage

**Expanded query set**
- Location: `testing/evaluation/queries.json`
- Target size: **100+ queries**
- Coverage balance:
  - **objects** — specific items, colors, attributes
  - **actions** — activities, movements, interactions
  - **scenes** — settings, contexts, environments
  - **explicit negatives** — queries with no relevant content in corpus
  - **near-misses** — wrong color, wrong setting, wrong activity, similar-but-not-matching

**Query schema**
```json
{
  "query_id": "q001",
  "query_text": "red car",
  "query_type": "object",
  "media_type_target": "image",
  "difficulty": "easy",
  "tags": ["color-specific", "vehicle"],
  "judged": true,
  "relevant_media_ids": [5],
  "relevant_scene_ids": [],
  "notes": "Exact color match required"
}
```

**Judgment policy**
- Binary relevance for Phase 7 (relevant or not relevant)
- No graded relevance yet (keeps judging simpler to maintain)
- For videos: allow both video-level and scene-level relevance where clear
- Explicit negative queries must have empty relevance lists
- Near-miss queries should have notes explaining why similar content is not relevant
- Every asset/query relationship must be double-checked manually by comparing the actual media content against the written judgment before the benchmark is accepted

**Coverage targets**
- Roughly even distribution across query types
- At least 20% explicit negative queries
- At least 15% near-miss queries
- Both image-only and video-only queries, plus mixed queries
- Range of difficulty levels (easy, medium, hard)

### 3.3 Evaluation Runner and Reporting

**Extended `evaluate_search.py`**

Current capabilities:
- Overall metrics (Precision@10, Recall@10, MRR, NDCG@10)
- Per-query results (optional)
- Per-type breakdown (optional)

New capabilities:
- **Modality slicing** — separate image/video metrics
- **Negative-query summaries** — false positive rates on explicit negatives
- **Difficulty slicing** — metrics by difficulty level
- **Baseline comparison** — structured diff against saved reports
- **Regression detection** — flag significant metric drops
- **Failure summaries** — categorize common failure modes

**Report structure**
```json
{
  "report_version": "1.0",
  "timestamp": "2026-05-02T10:30:00Z",
  "revision_label": "baseline-phase7",
  "corpus_version": "eval-v1",
  "query_set_version": "queries-v1",
  "overall": {
    "mean_precision@10": 0.65,
    "mean_recall@10": 0.85,
    "mean_mrr": 0.72,
    "mean_ndcg@10": 0.78,
    "num_queries": 105
  },
  "by_type": { ... },
  "by_modality": { ... },
  "by_difficulty": { ... },
  "negative_queries": {
    "num_queries": 22,
    "false_positive_rate": 0.05,
    "mean_false_positives_per_query": 0.3
  },
  "per_query": [ ... ]
}
```

**Baseline comparison**
- Save reports to `testing/evaluation/baselines/`
- Naming: `baseline-<revision-label>.json`
- Comparison output shows:
  - metric deltas
  - queries with large rank changes
  - new failures and fixes
  - overall verdict (improvement, regression, neutral)

**Regression detection**
- Flag if any core metric drops by more than a threshold (e.g., 5% relative)
- Flag if negative-query false positive rate increases significantly
- Flag if any query category regresses while others improve

### 3.4 Metrics History and Change Tracking

**Human-readable history document**
- Location: `docs/metrics/search_quality_history.md`
- Purpose: chronological log of algorithm changes and metric movements
- Format: append-only markdown

**Entry structure**
```markdown
## 2026-05-02 — Baseline Phase 7

**Revision:** baseline-phase7  
**Corpus:** eval-v1 (35 assets)  
**Queries:** queries-v1 (105 queries)

**Changes:**
- Established locked evaluation benchmark
- No algorithm changes in this baseline

**Metrics:**
- Precision@10: 0.65
- Recall@10: 0.85
- MRR: 0.72
- NDCG@10: 0.78

**By type:**
- Objects: P@10 0.68, R@10 0.88
- Actions: P@10 0.62, R@10 0.82
- Scenes: P@10 0.65, R@10 0.85

**Notable observations:**
- Negative queries: 5% false positive rate
- Video queries slightly weaker than image queries
- Near-miss queries show expected confusion

**Decision:** Baseline accepted
```

**Workflow after algorithm change**
1. Run evaluation in Docker against locked corpus
2. Save structured report with revision label
3. Compare against previous accepted baseline
4. Append history entry describing:
   - what changed in the algorithm
   - why the change was made
   - which metrics moved and by how much
   - which query categories improved or regressed
   - suspected causes of metric movements
   - decision (keep, tune further, or revert)

### 3.5 Test Coverage

**Expand `testing/evaluation/test_evaluate_search.py`**

Current coverage:
- Basic metric computation
- Query loading

New coverage:
- Asset manifest loading and validation
- Query schema validation
- Modality slicing
- Negative-query handling
- Baseline comparison logic
- Regression detection
- Report serialization and deserialization
- Failure summary generation

**Add integration test**
- `testing/evaluation/test_full_evaluation.py`
- Runs full evaluation against a tiny synthetic corpus
- Verifies end-to-end workflow including comparison and history update

## 4. Implementation Plan

### 4.1 Corpus and manifest
1. Create `testing/evaluation/assets/` directory
2. Download and add 35+ curated public media assets
   - Target: ~28 images, ~7 videos
   - Balanced content across objects, actions, scenes
   - Include some ambiguous or challenging content
3. Create `testing/evaluation/asset_manifest.json` with metadata for each asset
4. Commit assets and manifest to repository

### 4.2 Expanded query set
1. Expand `testing/evaluation/queries.json` to 100+ queries
2. Add new schema fields: `media_type_target`, `difficulty`, `tags`
3. Balance coverage across:
   - Query types (object, action, scene)
   - Explicit negatives (~20%)
   - Near-misses (~15%)
   - Difficulty levels
4. Add judging notes for clarity
5. Validate all judgments against the new corpus
6. Perform a strict manual double-check of asset authenticity and query judgments by reviewing the actual image and video content directly

### 4.3 Evaluation runner enhancements
1. Extend `evaluate_search.py` with:
   - Modality slicing
   - Difficulty slicing
   - Negative-query summaries
   - Baseline comparison
   - Regression detection
   - Failure summaries
2. Update report schema to include new sections
3. Add baseline loading and comparison logic
4. Add regression threshold configuration

### 4.4 Metrics history
1. Create `docs/metrics/` directory
2. Create `docs/metrics/search_quality_history.md`
3. Add initial baseline entry for Phase 7
4. Document the workflow for updating history after algorithm changes

### 4.5 Test coverage
1. Expand `testing/evaluation/test_evaluate_search.py`
2. Add `testing/evaluation/test_full_evaluation.py`
3. Add tests for:
   - Asset manifest validation
   - Query schema validation
   - New reporting features
   - Baseline comparison
   - Regression detection

### 4.6 Documentation
1. Update `docs/TASKS.md` with Phase 7 completion status
2. Update `docs/plan.md` with Phase 7 completion
3. Add evaluation workflow documentation to `docs/`

### 4.7 Baseline evaluation and documentation
1. Run the full evaluation against the locked corpus in Docker
2. Save the baseline report to `testing/evaluation/baselines/baseline-phase7.json`
3. Create the initial metrics history entry in `docs/metrics/search_quality_history.md`
4. Document the baseline metrics, corpus characteristics, and any notable observations

## 5. File Changes Summary

### New files
- `testing/evaluation/assets/` — locked benchmark corpus (35+ files)
- `testing/evaluation/asset_manifest.json` — asset metadata
- `testing/evaluation/baselines/` — saved evaluation reports
- `testing/evaluation/baselines/baseline-phase7.json` — initial baseline
- `docs/metrics/` — metrics history directory
- `docs/metrics/search_quality_history.md` — algorithm change log
- `testing/evaluation/test_full_evaluation.py` — integration test

### Modified files
- `testing/evaluation/queries.json` — expand to 100+ queries with new schema
- `testing/evaluation/evaluate_search.py` — add reporting and comparison features
- `testing/evaluation/test_evaluate_search.py` — broaden test coverage
- `testing/evaluation/run_evaluation.py` — standardize report output and comparison
- `docs/TASKS.md` — mark Phase 7 tasks complete
- `docs/plan.md` — update Phase 7 status

## 6. Success Criteria

### Corpus quality
- At least 35 local assets committed
- Asset mix is ~80% images, ~20% videos
- Asset manifest includes complete metadata for all files
- No runtime internet dependency for evaluation

### Query coverage
- At least 100 judged queries
- Balanced coverage across object/action/scene types
- At least 20% explicit negative queries
- At least 15% near-miss queries
- All judgments validated against the corpus
- Manual authenticity verification completed: every asset's actual content has been compared against its query judgments to ensure correctness

### Evaluation tooling
- Reports include overall, per-type, per-modality, per-difficulty, and negative-query metrics
- Baseline comparison works correctly
- Regression detection flags significant metric drops
- All new features have test coverage

### Metrics history
- History document exists with initial baseline entry
- Workflow for updating history is documented
- History format is clear and maintainable

### Baseline evaluation
- Baseline evaluation has been run against the locked corpus in Docker
- Baseline report saved to `testing/evaluation/baselines/baseline-phase7.json`
- Initial metrics history entry created in `docs/metrics/search_quality_history.md`
- Baseline metrics, corpus characteristics, and observations documented

### Testing
- All evaluation tests pass
- Integration test covers end-to-end workflow
- Docker-based evaluation runs successfully

## 7. Risks and Mitigations

### Risk: Corpus is too small to discriminate algorithm changes
**Mitigation:** Start with 35+ assets and 100+ queries; expand if metrics plateau or become noisy.

### Risk: Judging 100+ queries is time-consuming
**Mitigation:** Keep judgments binary (not graded); focus on clear cases; document ambiguous queries for future review.

### Risk: Baseline comparison is too sensitive or too lenient
**Mitigation:** Start with conservative regression thresholds (5% relative drop); tune based on experience.

### Risk: Metrics history becomes stale or inconsistent
**Mitigation:** Make history updates part of the algorithm change workflow; keep entries short and focused.

### Risk: Evaluation runs are too slow
**Mitigation:** Keep corpus size reasonable; optimize evaluation runner if needed; consider parallel query execution.

## 8. Future Work (Out of Scope for Phase 7)

- Media download/fetch tooling for expanding the corpus
- Production search logging hooks for online evaluation
- Graded relevance judgments (beyond binary)
- A/B testing infrastructure
- Automated query generation
- External vector database integration
- Advanced failure analysis and debugging tools

## 9. Definition of Done

Phase 7 is complete when:
- A locked local benchmark corpus of 35+ assets exists under `testing/evaluation/assets/`
- Asset manifest with complete metadata is committed
- Query set is expanded to 100+ judged queries with balanced coverage
- Manual authenticity verification completed: every asset's actual content has been compared against its query judgments to ensure correctness
- Evaluation runner produces overall, per-type, per-modality, per-difficulty, and negative-query reports
- Baseline comparison and regression detection work correctly
- Metrics history document exists with initial baseline entry
- Baseline evaluation has been run in Docker and documented with saved report and metrics history entry
- All evaluation tests pass
- Docker-based evaluation runs successfully
- Documentation is updated

## 10. Recommended Next Steps After Phase 7

1. Run baseline evaluation and establish initial metrics
2. Use the benchmark to validate any future ranking or retrieval changes
3. Consider future retrieval experiments only if evaluation evidence shows a specific truncation or candidate-recall problem
4. Consider caption quality improvements (Phase 10) if semantic coverage gaps are identified
5. Add production logging hooks (Phase 9) once the evaluation framework is stable
