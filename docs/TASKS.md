# Search Quality Improvement - Implementation Tasks

**Project Start:** 2026-04-30  
**Status:** Active work is **Phase 12 — accuracy audit remediation** (`docs/implementations/accuracy-audit-2026-05-29.md`). Earlier phases (1–7 complete, 8 reverted, 9–11 optional) live in git history.

---

## Phase 12 — Accuracy Audit Remediation

**Goal:** First make the evaluation trustworthy (Tier 0), then fix retrieval correctness/measurement, then upgrade model and representation, based on the 2026-05-29 audit. Full detail, root causes, and validation in `docs/implementations/accuracy-audit-2026-05-29.md`.

**Workflow:** Everything runs through **Docker Compose** (build, stack, evaluation, and tests — never host-local; see Notes → Execution environment), and independent tasks should be **fanned out to subagents**. One change at a time; re-run evaluation with `--compare-to baselines/baseline-phase7.json`; record accepted runs in `docs/metrics/search_quality_history.md` (per `docs/metrics/search_tuning_checklist.md`).

### Tasks
- [ ] 12.E1 Exclude negatives from P/R/MRR/NDCG means; keep them only in the negative summary; also cap MRR at k (`compute_metrics` currently scans the full retrieved list) (`evaluate_search`) `[P0]`
- [ ] 12.E2 Decouple `negative` from `difficulty: hard` so the hard slice measures answerable queries (`queries.json`) `[P0]`
- [ ] 12.E3 Make the negative metric threshold-aware (count only above-threshold hits as FPs; depends on A2) `[P0]`
- [ ] 12.E4 Add image (by-image) search coverage + a by-image `search_fn` (`run_evaluation.py`) `[P1]`
- [ ] 12.E5 Stabilize scene credit across re-seeding (media-level credit / pinned indices / re-validate labels) — ties to A1 `[P1]`
- [ ] 12.E6 Emit per-slice query counts; treat sub-5% deltas as noise (35-asset corpus, thin slices) `[P1]`
- [ ] 12.E7 Populate or remove the unused judgment-governance layer (`audit_log.json` is empty) `[P2]`
- [ ] 12.E8 Require explicit `--base-url` in documented eval commands and verify it reaches the gateway `[P2]`
- [ ] 12.A1 Verify eval can credit video/scene hits (runtime `scene:{filename}:{index}` vs `relevant_scene_ids`) — confirm which 0.0 slices are real; also check the `search_max_per_media=2` cap isn't dropping relevant scenes `[P0]`
- [ ] 12.A2 Add configurable relevance score threshold (`search_min_score`) in `search_service.py` / `config.py` — fixes negative FP rate + precision; apply the floor after diversity so the candidate pool isn't starved `[P0]`
- [ ] 12.A3 Fix fusion score-scale mismatch in `ranking_service.rank_candidates` (per-query normalization or Reciprocal Rank Fusion) `[P0]`
- [ ] 12.A4 Record metric-interpretation caveats (P@10 cap; prefer Recall/MRR/NDCG) in `docs/metrics/evaluation_benchmark_rubric.md` `[P1]`
- [ ] 12.B2 Add CLIP text prompt templating/ensembling in `clip_service.encode_text` `[P1]`
- [ ] 12.B3 Multi-frame scene representation (sample N frames, mean-pool) in `video_service.py` / `pipeline.py` `[P1]`
- [ ] 12.B4 Enrich keyword index (BM25 over tags / richer captions) in `index_service.py` `[P2]`
- [ ] 12.C1 Replace additive rerank boosts with a cross-encoder over top-K in `ranking_service.py` `[P2]`
- [ ] 12.C2 Fix caption pollution: stop indexing `"(scene N)"` disambiguation text (`pipeline._process_video`) `[P2]`

**Success Criteria:**
- Headline P/R/MRR/NDCG are computed over positive queries only, with negatives and the `hard` slice decoupled (E1–E2), so the numbers are trustworthy
- Negative false-positive rate drops well below `1.0` with no Recall@10/MRR/NDCG@10 regression on positive queries
- Video/Action slices are confirmed real and (where applicable) rise above `0`
- Each accepted change is evidenced against `baseline-phase7` and documented in the metrics history

**Order:** E1 → E2 → A1 → A2 → E3 → A3 → re-baseline → E4 → B2 → B3 → B4 → C1/C2  _(E3 follows A2: the threshold must exist first)_

---

## Notes

- **Current Phase:** Phase 12 — accuracy audit remediation (pending implementation)
- **Next Step:** Tier 0 (E1–E3) to make metrics trustworthy, then A1 → A2 → A3 and re-baseline before model upgrades
- **Execution environment:** The entire stack — build, run, evaluation, and tests — runs via **Docker Compose**; do not run services, the evaluation harness, or tests directly on the host. Use `docker compose` (stack: `docker compose up --build gateway-api search-api media-worker frontend`; tests: `docker compose --profile test run --rm --build service-tests`; evaluation/seeding: the `service-tests` profile per `docs/metrics/search_tuning_checklist.md`).
- **Execution strategy:** Prefer fanning out subagents to handle independent tasks in parallel.
