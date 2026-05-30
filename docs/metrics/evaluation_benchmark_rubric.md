# Evaluation Benchmark Rubric

**Version:** 2026-05-11

This rubric governs the locked Semedia evaluation benchmark.

## Relevance rules
- **Object queries:** the correct object class must be visually present.
- **Action queries:** the action must be visibly depicted, not merely implied.
- **Scene queries:** the judged scene key must match the canonical identifier exactly.

## Canonical scene key format
- Scene judgments use `scene:<filename>:<scene_index>`.
- The filename must be a video asset in the locked corpus.
- The scene index must be numeric.
- Legacy numeric-only scene ids are not valid for locked scene judgments.

## Caption audit statuses
- `usable`
- `weak-but-acceptable`
- `problematic`

## Escalation rules
- A problematic caption only blocks acceptance when it is linked to retrieval failures or measurable metric noise in the current run.
- When linked, the maintainer chooses `fix_in_place` or `remove`.
- Targeted reruns are the default remediation path for linked fixes.

## Metric interpretation caveats

- **Precision@10 is naturally low.** Most benchmark queries have only 1–2 relevant items, so the theoretical maximum P@10 is often 0.1–0.2. Do not treat low P@10 as a failure signal in isolation.
- **Primary signals:** Prefer Recall@10, MRR, and NDCG@10 as the main quality indicators — they are not capped by the small relevant-set size.
- **Headline means cover positive queries only.** Aggregate means (MRR, Recall@10, NDCG@10, P@10) are computed over positive queries exclusively. Negative-query performance (false-positive rate) is summarized separately in the report.

## Audit-log governance

The judgment-governance layer (`testing/evaluation/audit_log.json` + `benchmark_validation.py` sign-off logic) is **optional** and currently intentionally empty (`[]`). No entries are required for evaluation to run.

To adopt the governance layer, populate `audit_log.json` with entries containing these required fields:

| Field | Type | Description |
|-------|------|-------------|
| `reviewer` | string | Non-empty identifier of the person who reviewed the caption |
| `asset_id` | string or int | Media asset identifier |
| `scene_key` | string or null | Scene key in `scene:<filename>:<index>` format, or `null` for image assets |
| `caption_status` | string | One of `usable`, `weak-but-acceptable`, `problematic` |
| `linked_failure_query_ids` | list | Query IDs linked to retrieval failures (required non-empty when `caption_status` is `problematic`) |
| `disposition` | string | One of `accept`, `fix_in_place`, `remove` |
| `locked_at` | string | ISO-8601 timestamp of the review decision |

The `can_sign_off_benchmark` helper in `benchmark_validation.py` gates sign-off on structural validation passing and no unresolved `problematic` + `accept` entries.

## Acceptance gate
- Benchmark artifacts must validate before evaluation starts.
- A single benchmark maintainer signs off before the benchmark is tagged locked.
- Retrieval weights, embedding behavior, and ranking parameters are out of scope for benchmark lock decisions.
