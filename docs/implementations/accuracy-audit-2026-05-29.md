# Search Accuracy Audit & Remediation Plan

**Date:** 2026-05-29
**Baseline:** `baseline-phase7` (`testing/evaluation/baselines/baseline-phase7.json`)
**Status:** Documented — pending implementation
**Tracking:** Mirrored as Phase 12 in `docs/TASKS.md`

> Audit of the retrieval/ranking/embedding stack against the locked Phase 7 benchmark.
> Each item below has a stable ID (`A*` correctness/measurement, `B*` model/representation,
> `C*` reranking/hygiene). Apply one change at a time and re-run
> `run_evaluation.py --compare-to baseline-phase7.json` per `docs/metrics/search_tuning_checklist.md`.

---

## How the system works today

Upload → `pipeline.py` (BLIP caption + CLIP embed per image / per video keyframe) → two indexes:

- **Vector:** CLIP embeddings, cosine similarity via brute-force Python loop over all completed media (`search_service._vector_results`).
- **Keyword:** TF-IDF (1–2 grams, 10k features, english stopwords) cosine over BLIP captions (`index_service`).

Query time (`ranking_service.rank_candidates`): `fusion = 0.7·vector + 0.3·keyword` → additive boosts (+0.08 exact phrase, +0.02 caption >50 chars) → diversity cap (2/media, caption dedupe) → top-k.

## Baseline numbers (and how to read them)

P@10 `0.0467`, R@10 `0.4292`, MRR `0.3109`, NDCG@10 `0.3309`, negative FP rate `1.0000`; Actions / Videos / Hard slices all `0.0000`.

Two of these alarms are measurement/calibration artifacts, not pure model failure — and the headline itself is depressed by negatives mixed into the means. Fix the evaluation framework first (**Tier 0: E1–E3**), then A1/A4, so model tuning is judged against trustworthy numbers.

---

## Tier 0 — Evaluation framework capability (prerequisite)

**Verdict: partially capable.** Strengths: evaluation runs against the **live stack** over HTTP (`run_evaluation.search_text_via_api` → `/api/v1/search/`, not a mock), the corpus is locked (`asset_manifest.json` + manifest-lock test), structural validation is strong (`benchmark_validation`: schema, enums, `scene_key` format, no unmanifested/missing assets), and there are type/modality/difficulty/negative slices plus a regression gate.

**But the current numbers are not trustworthy yet**, and several retrieval paths are unmeasured. Fix E1–E3 before trusting any A/B/C metric. Dataset facts (measured): 120 queries, 35 assets, 34 action, 26 hard, ~23 negative.

### E1 — Negatives are folded into the headline means `[priority: P0] [status: TODO]`
- **Finding:** ~23 of 120 judged queries are negatives (`judged: true`, empty `relevant_media_ids`/`relevant_scene_ids`). They are averaged into P/R/MRR/NDCG, each forced to `0`, so ~19% of the headline is structural zeros — positive-query performance is materially higher than the `R@10 0.43 / MRR 0.31` headline.
- **Fix:** Compute P/R/MRR/NDCG over **positive** queries only; negatives feed only the negative-FP summary.
- **Location:** `evaluate_search.run_evaluation` mean aggregation.
- **Validation:** Positive-only means rise; negative count no longer affects them.

### E2 — "Hard" slice is dominated by negatives `[priority: P0] [status: TODO]`
- **Finding:** The ~23 negatives are all tagged `difficulty: hard`, so the hard slice (26) is ~88% negatives. Its uniform `0.0` measures abstention, **not** hard-but-answerable retrieval — the slice is currently meaningless for its stated purpose.
- **Fix:** Separate the negative tag from difficulty; ensure each difficulty slice contains positive queries.
- **Location:** `queries.json` + slice summarization.
- **Validation:** Hard slice contains positive queries and reports non-trivial metrics.

### E3 — Negative metric is not threshold/relevance aware `[priority: P0] [status: TODO]`
- **Finding:** `summarize_negative_queries` counts *any* returned id as a false positive, so the rate is pinned at `1.0` regardless of result quality (uninformative until A2 lands).
- **Fix:** After A2, count only results **above threshold** as false positives; also report the score distribution of negatives' top hit.
- **Location:** `summarize_negative_queries` (depends on A2).
- **Validation:** Rate becomes sensitive to the threshold and to ranking quality.

### E4 — The image (by-image) search path is never evaluated `[priority: P1] [status: TODO]`
- **Finding:** `run_evaluation` only calls text search; `search_image` / `/api/v1/search/by-image/` has zero benchmark coverage.
- **Fix:** Add image-query cases and a by-image `search_fn`.
- **Location:** `run_evaluation.py`, `queries.json`.
- **Validation:** Image-query metrics are reported.

### E5 — Scene credit is fragile across re-seeding `[priority: P1] [status: TODO]`
- **Finding:** `relevant_scene_ids` encode a `scene_index` from one detection run. The tuning checklist instructs re-seeding after scene-threshold changes, which silently shifts indices and breaks previously-correct labels.
- **Fix:** Credit at media level, or pin scene indexing, or re-validate labels after every re-seed. Ties to A1.
- **Location:** `_result_identifier` / seed flow.
- **Validation:** Changing scene threshold + re-seed does not invalidate video credit.

### E6 — Low statistical power; noisy regression gate `[priority: P1] [status: TODO]`
- **Finding:** 35 assets, many queries with a single relevant item, thin slices; the 5% relative regression gate has no variance/CI and will be noisy. (Minor: MRR scans the full retrieved list, not `@k` — benign while `top_k=10`.)
- **Fix:** Expand corpus/queries where feasible; emit per-slice query counts; treat sub-5% deltas as noise, not signal.
- **Validation:** Reports include slice `num_queries`; gate documented as indicative.

### E7 — Judgment governance unused `[priority: P2] [status: TODO]`
- **Finding:** `audit_log.json` is empty, so the reviewer sign-off / problematic-caption blockers the validator supports are inert. Single annotator, binary relevance, no pooling — unlabeled-but-relevant items are scored as false positives.
- **Fix:** Populate the audit log or drop the unused layer; consider graded relevance / pooling.
- **Validation:** Either the governance layer is exercised or removed; judging method documented.

### E8 — Verify the documented run command reaches the gateway `[priority: P2] [status: TODO]`
- **Finding:** `run_evaluation` defaults to `--base-url http://127.0.0.1:8000`, but the tuning checklist invokes it inside the `service-tests` container without `--base-url`; seeding uses `http://gateway-api:8000`. Confirm the default resolves to the gateway from inside that container.
- **Fix:** Require/document an explicit `--base-url` in the checklist commands.
- **Validation:** Documented command provably hits the running gateway.

---

## Tier 1 — Retrieval correctness & measurement (highest ROI)

### A1 — Verify the eval can credit video/scene hits `[priority: P0] [status: TODO]`
- **Finding:** Every video/action slice scores exactly `0.0`. A uniform zero across an entire modality is more consistent with an identifier mismatch than with the model getting nothing right.
- **Root cause (hypothesis):** Video credit requires an exact match between runtime `_stable_scene_key` = `scene:{original_filename}:{scene_index}` (`search_service.py`) and the benchmark `relevant_scene_ids`, e.g. `scene:vid-campfire-01.webm:1` (`queries.json`). The match is brittle on two axes: stored `original_filename` must be identical, and `scene_index` numbering must align with however many scenes `ContentDetector` produced when the labels were authored (q028 expects index `1`, not `0`).
- **Action:** Run one known video query (e.g. `campfire`, `bird in flight`) and print retrieved `scene_key`s next to the expected ids. Confirm whether the 0.0s are real retrieval failures or key mismatches.
- **Validation:** A single video query returns a `scene_key` that string-equals its `relevant_scene_ids` entry.

### A2 — Add a relevance score threshold `[priority: P0] [status: TODO]`
- **Finding:** Negative FP rate is pinned at `1.0`; precision is very low.
- **Root cause:** `search_text` / `search_image` always return the top-k regardless of score; there is no minimum-score cutoff anywhere in the path. `summarize_negative_queries` counts any returned id as a false positive, so a negative query can never beat `1.0`.
- **Fix:** Introduce a configurable minimum score (vector floor ~0.22–0.26 on raw CLIP cosine, plus a fusion floor). Return fewer/zero results when nothing clears the bar.
- **Location:** `search_service.py` (apply after ranking), `config.py` (new `search_min_score` setting).
- **Validation:** Negative FP rate drops well below `1.0` with no R@10/MRR/NDCG regression on positive queries.

### A3 — Fix the fusion score-scale mismatch `[priority: P0] [status: TODO]`
- **Finding:** The `0.7/0.3` fusion weights do not behave as 70/30 in practice.
- **Root cause:** `_normalize_scores` only **clamps** to `[0,1]`; it never rescales. CLIP cosine is compressed (~0.2–0.35 for true matches) while TF-IDF cosine reaches ~0.8–1.0 on short-caption exact matches, so keyword silently dominates whenever it fires.
- **Fix:** Either min-max normalize each signal per query before fusing, or switch to **Reciprocal Rank Fusion** (rank-based, scale-free). RRF is the recommended default for hybrid search.
- **Location:** `ranking_service.rank_candidates` (+ `_normalize_scores` in `search_service.py`).
- **Validation:** MRR / NDCG@10 improve vs baseline; fusion weight changes produce the expected directional effect.

### A4 — Record metric-interpretation caveats `[priority: P1] [status: TODO]`
- **Finding:** P@10 is capped low by the benchmark itself — most queries have 1–2 relevant items, so max P@10 is often `0.1`.
- **Fix:** Add a short note to `docs/metrics/evaluation_benchmark_rubric.md`: treat Recall@10 / MRR / NDCG@10 as primary; read P@10 relative to the per-query relevant count.
- **Validation:** Note present; future entries reference the right primary metrics.

---

## Tier 2 — Model & representation (real semantic gains)

### B2 — CLIP text prompt templating/ensembling `[priority: P1] [status: TODO]`
- **Finding:** Bare query strings (`"castle"`) are embedded directly.
- **Root cause:** CLIP was trained on `"a photo of a {x}"`; bare tokens underperform.
- **Fix:** Wrap/ensemble query text over a few templates in `clip_service.encode_text`. Near-free.
- **Validation:** Object/scene-query MRR improves with no regression elsewhere.

### B3 — Multi-frame scene representation `[priority: P1] [status: TODO]`
- **Finding:** Actions and video recall are weakest.
- **Root cause:** `extract_scene_keyframe` samples a single midpoint frame; one static frame loses motion.
- **Fix:** Sample N frames/scene and mean-pool embeddings (and/or caption the best frame).
- **Location:** `video_service.py`, `pipeline._process_video`.
- **Validation:** Video modality + Action type rise above `0` (after A1 is cleared).

### B4 — Enrich the keyword index `[priority: P2] [status: TODO]`
- **Finding:** Keyword recall is capped by short BLIP captions — missing words ⇒ zero keyword recall.
- **Fix:** Switch TF-IDF cosine → **BM25** (better for short docs) over richer text: object / zero-shot CLIP tags or BLIP-2 captions.
- **Location:** `index_service.py`. Overlaps existing Phase 10.1 / 11.2.
- **Validation:** Keyword-driven recall improves on hard queries without raising negative FPs.

---

## Tier 3 — Reranking & hygiene

### C1 — Stronger reranker over top-K `[priority: P2] [status: TODO]`
- **Finding:** Additive boosts (+0.08 / +0.02) are negligible against ~0.3 fusion scores.
- **Fix:** Re-rank top-K with a cross-encoder (query↔caption) instead of constant boosts.
- **Location:** `ranking_service.py`.
- **Validation:** P@10 / NDCG improve on the top page.

### C2 — Fix caption pollution `[priority: P2] [status: TODO]`
- **Finding:** `pipeline._process_video` appends `"(scene N)"` to disambiguate adjacent identical captions, then that text is indexed by TF-IDF, injecting noise tokens.
- **Fix:** De-duplicate at storage/ranking time; keep the indexed caption clean.
- **Location:** `pipeline._process_video`, `index_service.build_keyword_index`.
- **Validation:** No `"(scene N)"` tokens in the index; keyword behavior unchanged or better.

---

## Out of scope (already tracked)

- Brute-force in-memory cosine scan (`_vector_results`) is a **scalability**, not accuracy, concern → existing Phase 11.1 (pgvector/FAISS).

## Suggested order

E1 → E2 (trustworthy metrics) → A1 (verify scene credit) → A2 (threshold) → E3 (threshold-aware negatives) → A3 (fusion/RRF) → re-baseline → E4 (image eval) → B2 → B3 → B4 → C1/C2.
One change at a time; `--compare-to baseline-phase7.json`; record accepted runs in `docs/metrics/search_quality_history.md`.

---

## Review addenda (2026-05-30)

A read-only subagent review confirmed both headline claims against code: `evaluate_search.run_evaluation` averages negatives (judged, empty relevant lists) into the means, and `search_service._normalize_scores` only clamps so `ranking_service.rank_candidates` fuses un-rescaled CLIP cosine with TF-IDF. Plan adjustments:

- **Ordering:** E3 depends on A2 (needs the threshold) — sequence E3 **after** A2.
- **A1+:** also check the `search_max_per_media=2` diversity cap isn't dropping relevant video scenes — an alternate cause of video-recall zeros, independent of the scene-key mismatch.
- **A2+:** apply the score floor **after** diversity so `search_candidate_multiplier` doesn't starve the pool below `limit`.
- **E1+:** cap MRR at k (`compute_metrics` scans the full retrieved list — benign at `top_k=10`, latent bug otherwise).
- **Defer:** B4, C1, and E7 are low-leverage for a 35-asset corpus; revisit after E1+A2+A3 re-baseline.
