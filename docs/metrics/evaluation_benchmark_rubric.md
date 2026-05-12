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

## Acceptance gate
- Benchmark artifacts must validate before evaluation starts.
- A single benchmark maintainer signs off before the benchmark is tagged locked.
- Retrieval weights, embedding behavior, and ranking parameters are out of scope for benchmark lock decisions.
