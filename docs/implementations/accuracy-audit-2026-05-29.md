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

Two of these alarms are measurement/calibration artifacts, not pure model failure. Fix measurement first (A1, A4) so model tuning is judged against trustworthy numbers.

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

### B1 — Upgrade the CLIP model `[priority: P1] [status: TODO]`
- **Finding:** Default `openai/clip-vit-base-patch16` is the weakest supported retrieval backbone.
- **Fix:** Move to `openai/clip-vit-large-patch14` (or a LAION/SigLIP checkpoint). Biggest single-knob semantic gain; loader + README already support large variants.
- **Location:** `CLIP_MODEL_NAME` env / `config.py`. Requires corpus re-embed + re-seed; mind VRAM.
- **Validation:** R@10 / NDCG improve; document VRAM/latency cost.

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

A1 (verify) → A2 (threshold) → A3 (fusion/RRF) → re-baseline → B1 + B2 → B3 → B4 → C1/C2.
One change at a time; `--compare-to baseline-phase7.json`; record accepted runs in `docs/metrics/search_quality_history.md`.
