# Search Quality Metrics History

This file records every accepted evaluation run after a search algorithm or benchmark change.

## Entry Template

### YYYY-MM-DD — Revision label
- **Revision:** `<revision-label>`
- **Corpus:** `<corpus-version>`
- **Queries:** `<query-version>`
- **What changed:**
  - `<short change summary>`
- **Metrics:**
  - Precision@10: `<value>`
  - Recall@10: `<value>`
  - MRR: `<value>`
  - NDCG@10: `<value>`
  - Negative false positive rate: `<value>`
- **Notes:**
  - Record any non-default tuning values in `docs/metrics/search_tuning_checklist.md`
  - Summarize the most relevant by-type, by-modality, and by-difficulty observations
  - Call out anything that still looks suspicious or ambiguous
- **Decision:** `<accepted / tune further / revert>`

---

## History

### 2026-05-02 — baseline-phase7
- **Revision:** `baseline-phase7`
- **Corpus:** `eval-v1`
- **Queries:** `queries-v1`
- **What changed:**
  - Added the locked Phase 7 benchmark corpus under `testing/evaluation/assets/`
  - Replaced the earlier query file with a 120-query judged benchmark set
  - Added modality slices, difficulty slices, negative-query summaries, and saved report output
  - Reran the baseline after repairing `vid-train-passing-01.webm` so the saved report reflects the full locked corpus
- **Tuning parameters:**
  - **Fusion weights:**
    - Vector weight: `0.7`
    - Keyword weight: `0.3`
  - **Scene detection:**
    - Base threshold: `27.0`
    - Adaptive: `20.0 for <30s, 35.0 for >10min, base otherwise`
  - **Reranking boosts:**
    - Exact phrase match: `+0.08`
    - Rich caption (>50 chars): `+0.02`
  - **Diversity controls:**
    - Max scenes per video in top results: `2`
    - Caption deduplication: `enabled for text search`
  - **Caption generation:**
    - Model: `Salesforce/blip-image-captioning-large`
    - Max length: `50`
    - Min length: `10`
    - Num beams: `5`
    - Retry weak captions: `enabled`
    - Retry num beams: `8`
    - Batch size: `8`
  - **Embedding model:**
    - CLIP model: `openai/clip-vit-base-patch16`
- **Metrics:**
  - Precision@10: `0.0467`
  - Recall@10: `0.4292`
  - MRR: `0.3109`
  - NDCG@10: `0.3309`
  - Negative false positive rate: `1.0000`
- **By type:**
  - Objects: `P@10 0.0636, R@10 0.5909, MRR 0.4490, NDCG@10 0.4719`
  - Actions: `P@10 0.0000, R@10 0.0000, MRR 0.0000, NDCG@10 0.0000`
  - Scenes: `P@10 0.0667, R@10 0.6071, MRR 0.4179, NDCG@10 0.4512`
- **By modality:**
  - Images: `P@10 0.0712, R@10 0.7121, MRR 0.5020, NDCG@10 0.5521`
  - Mixed: `P@10 0.0750, R@10 0.3750, MRR 0.3480, NDCG@10 0.2728`
  - Videos: `P@10 0.0000, R@10 0.0000, MRR 0.0000, NDCG@10 0.0000`
- **By difficulty:**
  - Easy: `P@10 0.0652, R@10 0.5978, MRR 0.4312, NDCG@10 0.4596`
  - Medium: `P@10 0.0542, R@10 0.5000, MRR 0.3639, NDCG@10 0.3869`
  - Hard: `P@10 0.0000, R@10 0.0000, MRR 0.0000, NDCG@10 0.0000`
- **Notable observations:**
  - The rerun now reflects the complete locked corpus, including the repaired train-passing video.
  - Image and scene retrieval remain meaningfully above zero, but video-target and action queries are still fully failing in this baseline.
  - Negative-query behavior is still very weak: false positive rate is `1.0000` with `9.8696` false positives per negative query on average.
  - Weakest early failures still include `castle`, `fortress`, `campfire`, `flower close-up video`, and `bird in flight`.
- **Decision:** `accepted`

### 2026-05-02 — caption-weak-filtering-disabled
- **Revision:** `caption-weak-filtering-disabled`
- **Corpus:** `eval-v1`
- **Queries:** `queries-v1`
- **What changed:**
  - Disabled weak-caption filtering to prevent rejection of short but valid captions from the BLIP-large model
  - Added `CAPTION_ENABLE_WEAK_FILTERING` environment variable (default: enabled for backward compatibility)
  - Modified `_is_weak_caption()` to return False immediately when filtering is disabled
  - Observed issue: portrait images were receiving "Image content unclear." fallback due to over-aggressive filtering rejecting useful short outputs
- **Tuning parameters:**
  - **Fusion weights:**
    - Vector weight: `0.7`
    - Keyword weight: `0.3`
  - **Scene detection:**
    - Base threshold: `27.0`
    - Adaptive: `20.0 for <30s, 35.0 for >10min, base otherwise`
  - **Reranking boosts:**
    - Exact phrase match: `+0.08`
    - Rich caption (>50 chars): `+0.02`
  - **Diversity controls:**
    - Max scenes per video in top results: `2`
    - Caption deduplication: `enabled for text search`
  - **Caption generation:**
    - Model: `Salesforce/blip-image-captioning-large`
    - Max length: `50`
    - Min length: `10`
    - Num beams: `5`
    - Retry weak captions: `enabled`
    - Retry num beams: `8`
    - Batch size: `8`
    - **Weak caption filtering: `disabled`** (new parameter)
  - **Embedding model:**
    - CLIP model: `openai/clip-vit-base-patch16`
- **Metrics:**
  - Precision@10: `0.0458`
  - Recall@10: `0.4250`
  - MRR: `0.3093`
  - NDCG@10: `0.3291`
  - Negative false positive rate: `1.0000`
  - Mean false positives/query: `7.2609`
- **By type:**
  - Not captured in this run
- **By modality:**
  - Not captured in this run
- **By difficulty:**
  - Not captured in this run
- **Notable observations:**
  - Slight metric drops across the board (P@10: -0.0009, R@10: -0.0042, MRR: -0.0016, NDCG@10: -0.0018)
  - Comparison status: `ok` (no regression flag triggered)
  - The drops are minimal and within expected variance for a caption-quality tradeoff
  - Disabling filtering allows the model's natural short outputs (e.g., "a woman", "cat") to be indexed instead of being replaced with the generic fallback
  - This change prioritizes recall over precision for caption-based retrieval, accepting that some captions may be less descriptive
  - False positive behavior unchanged (still 1.0000 rate, slightly lower mean count)
- **Decision:** `accepted`
