# Search Tuning Checklist

This document provides a systematic process for tuning search ranking parameters using the Phase 7 evaluation framework.

## Overview

The Semedia search system has several tunable parameters that affect retrieval quality. Changes should be evaluated against the locked benchmark corpus before adoption to ensure improvements are measurable and regressions are caught early.

## Tuning Workflow

For every parameter change:

1. **Baseline measurement** — Run evaluation against current settings and save the report
2. **Change one parameter** — Modify a single weight, threshold, or rule
3. **Rebuild and restart** — Apply the change to the running stack
4. **Run evaluation** — Generate a new report with `--compare-to` pointing to the baseline
5. **Review metrics** — Check overall metrics and grouped summaries (by type, modality, difficulty)
6. **Accept or revert** — If metrics improve without regressions, accept and document in `docs/metrics/search_quality_history.md`; otherwise revert

**Golden rule:** Change one parameter at a time. Bundled changes make it impossible to isolate what worked.

## Parameter Categories

### 1. Fusion Weights

**What they control:** How vector similarity and keyword similarity are combined into the final ranking score.

**Current defaults:**
- `SEARCH_VECTOR_WEIGHT=0.7`
- `SEARCH_KEYWORD_WEIGHT=0.3`

**Where to change:**
- Environment variables in `docker-compose.yml` or `.env`
- Defaults in `services/shared/semedia_shared/config.py`

**Tuning process:**

1. Run baseline evaluation:
   ```bash
   docker compose --profile test run --rm service-tests \
     python testing/evaluation/run_evaluation.py \
     --queries testing/evaluation/queries.json \
     --output testing/evaluation/baselines/current.json
   ```

2. Adjust weights in `docker-compose.yml`:
   ```yaml
   environment:
     SEARCH_VECTOR_WEIGHT: "0.6"
     SEARCH_KEYWORD_WEIGHT: "0.4"
   ```

3. Restart the stack:
   ```bash
   docker compose down
   docker compose up -d --build gateway-api search-api media-worker frontend
   ```

4. Run evaluation with comparison:
   ```bash
   docker compose --profile test run --rm service-tests \
     python testing/evaluation/run_evaluation.py \
     --queries testing/evaluation/queries.json \
     --output testing/evaluation/baselines/tuned.json \
     --compare-to testing/evaluation/baselines/current.json
   ```

5. Review the comparison output:
   - Check `Comparison status: ok` or `regression`
   - Look at deltas for `mean_precision@10`, `mean_recall@10`, `mean_mrr`, `mean_ndcg@10`
   - Check grouped summaries (by type, modality, difficulty) for uneven impact

6. If metrics improve:
   - Commit the weight change
   - Document in `docs/metrics/search_quality_history.md` with the new report
   - Save the tuned report as the new baseline

**What to watch:**
- Increasing vector weight helps queries where captions are weak or generic
- Increasing keyword weight helps queries with strong exact-match terms
- Check negative-query false positive rate — keyword weight increases can raise false positives if captions are noisy

### 2. Reranking Boosts

**What they control:** Score adjustments applied after fusion to promote high-confidence matches.

**Current defaults:**
- Exact phrase match boost: `+0.08`
- Rich caption boost (>50 chars): `+0.02`

**Where to change:**
- Constants in `services/shared/semedia_shared/ranking_service.py`

**Tuning process:**

1. Run baseline evaluation (same as fusion weights step 1)

2. Edit `services/shared/semedia_shared/ranking_service.py`:
   ```python
   _EXACT_PHRASE_BOOST = 0.10
   _RICH_CAPTION_BOOST = 0.03
   ```

3. Rebuild and restart:
   ```bash
   docker compose down
   docker compose up -d --build gateway-api search-api media-worker frontend
   ```

4. Run evaluation with comparison (same as fusion weights step 4)

5. Review metrics:
   - Exact phrase boost primarily affects precision
   - Rich caption boost affects recall for descriptive captions
   - Check by-type summaries: object queries often benefit more from exact match, scene queries from richer captions

6. If metrics improve, commit and document

**What to watch:**
- Exact phrase boost too high can over-promote keyword matches at the expense of semantic similarity
- Rich caption boost too high can bias toward verbose captions that are not necessarily better
- Check per-query results for regressions masked by aggregate improvements

### 3. Scene Detection Thresholds

**What they control:** How aggressively videos are split into scenes. Lower thresholds create more scenes, higher thresholds create fewer scenes.

**Current defaults:**
- Base threshold: `27.0`
- Adaptive thresholds:
  - Videos <30s: `20.0`
  - Videos >10min: `35.0`
  - Otherwise: base threshold

**Where to change:**
- Environment variable `SCENE_DETECTION_THRESHOLD` in `docker-compose.yml` or `.env`
- Adaptive logic in `services/shared/semedia_shared/video_service.py`

**Tuning process:**

1. Run baseline evaluation (same as fusion weights step 1)

2. Adjust threshold in `docker-compose.yml`:
   ```yaml
   environment:
     SCENE_DETECTION_THRESHOLD: "30.0"
   ```

3. Rebuild and restart the stack:
   ```bash
   docker compose down
   docker compose up -d --build gateway-api search-api media-worker frontend
   ```

4. Re-seed the evaluation corpus so videos are reprocessed with the new threshold:
   ```bash
   docker compose --profile test run --rm service-tests \
     python testing/evaluation/seed_media.py
   ```

5. Run evaluation with comparison (same as fusion weights step 4)

6. Review metrics:
   - Check video-target query performance in by-modality summary
   - Check action-query performance in by-type summary
   - Look at per-query results for video queries that improved or regressed

7. If metrics improve, commit and document

**What to watch:**
- Lower thresholds can improve recall but hurt precision through near-duplicate scenes
- Higher thresholds can improve precision but miss short actions or transitions
- Only tune these when video retrieval is the clear weak point

### 4. Diversity Controls

**What they control:** How many scenes from the same video can appear in top results.

**Current defaults:**
- Max scenes per video in top results: `2`
- Caption deduplication: enabled for text search

**Where to change:**
- Environment variable `SEARCH_MAX_PER_MEDIA` in `docker-compose.yml` or `.env`
- Diversity logic in `services/shared/semedia_shared/ranking_service.py`

**Tuning process:**

1. Run baseline evaluation (same as fusion weights step 1)

2. Adjust max scenes per video in `docker-compose.yml`:
   ```yaml
   environment:
     SEARCH_MAX_PER_MEDIA: "3"
   ```

3. Rebuild and restart:
   ```bash
   docker compose down
   docker compose up -d --build gateway-api search-api media-worker frontend
   ```

4. Run evaluation with comparison (same as fusion weights step 4)

5. Review metrics:
   - Check recall@10 for gains from multiple relevant scenes in one video
   - Check precision@10 for losses from duplicate-heavy pages
   - Look at per-query results for queries dominated by one video

6. If metrics improve, commit and document

**What to watch:**
- Increasing the cap helps when one video has multiple distinct relevant scenes
- Increasing the cap hurts when one video has many near-duplicate scenes that crowd out other media
- Caption deduplication remains a separate control

## Evaluation Commands Reference

### Run evaluation and save report

```bash
docker compose --profile test run --rm service-tests \
  python testing/evaluation/run_evaluation.py \
  --queries testing/evaluation/queries.json \
  --output testing/evaluation/baselines/report-YYYY-MM-DD.json
```

### Run evaluation with baseline comparison

```bash
docker compose --profile test run --rm service-tests \
  python testing/evaluation/run_evaluation.py \
  --queries testing/evaluation/queries.json \
  --output testing/evaluation/baselines/report-YYYY-MM-DD.json \
  --compare-to testing/evaluation/baselines/baseline-phase7.json
```

### Seed the evaluation corpus

```bash
docker compose --profile test run --rm service-tests \
  python testing/evaluation/seed_media.py
```

## Metrics Interpretation

### Overall Metrics

- **Precision@10:** Fraction of top-10 results that are relevant. Higher is better.
- **Recall@10:** Fraction of all relevant items that appear in top-10. Higher is better.
- **MRR:** Average of `1 / rank` for the first relevant result. Higher is better.
- **NDCG@10:** Rewards relevant results appearing earlier. Higher is better.
- **Negative false positive rate:** Fraction of negative queries that return any results. Lower is better.

### Grouped Summaries

- **By type (object, action, scene):** Reveals which query classes are weak
- **By modality (image, video, mixed):** Reveals whether image or video retrieval is weak
- **By difficulty (easy, medium, hard):** Reveals whether the system handles ambiguous or rare queries

### Regression Detection

The `--compare-to` flag computes deltas and flags regressions:
- A metric is flagged as a regression if it drops by more than 5% relative to the baseline
- Negative false positive rate is flagged if it increases by more than 0.05 absolute

If `Comparison status: regression` appears, inspect the `regressions` list and `deltas` before accepting the change.

## Documentation Requirements

After accepting a tuning change, document it in `docs/metrics/search_quality_history.md`:

1. Add a new entry with the date and revision label
2. Describe exactly what changed
3. Copy the full tuning-parameters block for reproducibility
4. Record the metrics and grouped summaries
5. Add notable observations and the decision

## Common Pitfalls

- Changing multiple parameters at once
- Skipping the baseline run
- Ignoring grouped summaries
- Tuning on a single query
- Accepting changes without updating `docs/metrics/search_quality_history.md`
- Forgetting to re-seed after scene-detection changes

## Next Steps

Once you've accepted a tuning change:

1. Run the full service test suite:
   ```bash
   docker compose --profile test run --rm --build service-tests
   ```
2. Keep the updated metrics history entry and accepted baseline report together with the tuning change
3. Revisit future retrieval experiments only if measured evidence justifies them after the accepted Phase 7 baseline and later tuning work
