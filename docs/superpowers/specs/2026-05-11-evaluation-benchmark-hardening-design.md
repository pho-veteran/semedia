# Evaluation Benchmark Hardening

**Date:** 2026-05-11  
**Status:** Approved design  
**Scope:** Harden the Semedia evaluation benchmark so its judgments, caption audits, and evaluator behavior are trustworthy enough to support future search-quality work.

## 1. Objectives

This revision strengthens benchmark rigor without expanding the corpus or tuning retrieval behavior.

### Primary goals
- Make benchmark judgments consistent and reviewable through an explicit rubric
- Enforce one canonical scene-key format end to end
- Add a structured caption-audit and escalation flow to the benchmark lock process
- Ensure benchmark artifacts are schema-valid before evaluation begins
- Make benchmark acceptance reproducible through a named maintainer sign-off flow

### Non-goals
- No retrieval-model tuning
- No changes to embedding generation logic
- No ranking-weight or reranking-parameter tuning
- No benchmark corpus expansion unless a later revision explicitly scopes it
- No retrieval-side investigations folded into this hardening pass just because smoke validation surfaces unrelated metric movement

## 2. Current State and Problem Statement

The current benchmark is already local, reproducible, and judged, but it still has rigor gaps that can make metrics harder to trust.

### Observed benchmark concerns
- Negative-query behavior remains very weak in the accepted baseline, with false positive rate still recorded as `1.0000` in `docs/metrics/search_quality_history.md`
- The corpus is intentionally small, which makes consistency and evaluator correctness more important than breadth in this revision
- Caption quality is not yet treated as a first-class audited artifact during benchmark lock

### Observed evaluator correctness concern
The current evaluation stack appears to mix two scene-identifier models:
- the benchmark dataset and newer tests use stable scene keys like `scene:vid-train-passing-01.webm:1`
- the evaluator still contains legacy logic that wraps `relevant_scene_ids` as `scene:{item_id}`

This mismatch must be treated as a benchmark-rigor issue because incorrect scene-key matching can create false misses and distort downstream caption-audit conclusions.

## 3. Benchmark Contract

The locked benchmark remains roughly the current size, but its acceptance bar becomes stricter.

### 3.1 Retrieval-judgment policy
The benchmark continues to use binary relevance judgments.

Judgment rubric skeleton:
- **Object queries:** the correct object class must be visually present
- **Action queries:** the action must be visually depicted, not merely implied
- **Scene queries:** the judged scene key must match the canonical identifier, not a legacy numeric ID

### 3.2 Caption-audit policy
Caption audit becomes a first-class benchmark-lock step, but problematic captions are blockers only when they can be directly linked to retrieval failures or measurable metric noise.

Caption status values:
- `usable`
- `weak-but-acceptable`
- `problematic`

A caption marked `problematic` does **not** automatically block acceptance. It blocks only when the benchmark maintainer can connect it to retrieval misses, false positives, or other measurable evaluation distortion in the current run.

### 3.3 Caption-audit ownership
The human reviewer performs the caption audit as part of benchmark lock review after retrieval judgments are finalized but before the benchmark is accepted.

### 3.4 Escalation policy
When a problematic caption is linked to measured benchmark distortion:
- the benchmark maintainer cross-checks it against the current evaluation run
- the outcome is either `fix_in_place` or `remove`
- the turnaround window is one revision cycle before the affected asset is cleared or dropped

## 4. Benchmark Artifacts

This revision keeps benchmark responsibilities split across explicit artifacts.

### 4.1 Retrieval ground truth
`testing/evaluation/queries.json` remains the retrieval ground-truth artifact, but its schema should evolve from a top-level raw array into a metadata-bearing object so it can declare the judgment policy explicitly.

Target shape:
- top-level `judgment_policy` object containing:
  - `path`
  - `version`
- top-level `queries` array containing the existing judged-query entries

This makes the governing policy explicit for every locked revision.

### 4.2 Corpus inventory
`testing/evaluation/asset_manifest.json` remains the locked corpus inventory.

### 4.3 Benchmark audit log
Add `testing/evaluation/audit_log.json` as the benchmark lock artifact for caption audit and escalation history.

Each audit entry must require:
- `reviewer`
- `asset_id`
- `scene_key`
- `caption_status`
- `linked_failure_query_ids`
- `disposition`
- `locked_at`

Schema rules:
- `scene_key` is required but may be `null` for image-only or asset-level reviews that do not target a specific scene
- `caption_status` must be one of `usable`, `weak-but-acceptable`, `problematic`
- `linked_failure_query_ids` must always be present as a list, even when empty
- `disposition` must be one of `accept`, `fix_in_place`, `remove`
- `locked_at` must be a timestamp so revision history is traceable

### 4.4 Judgment rubric doc
The canonical rubric document lives under `docs/metrics/`.

It defines:
- object, action, and scene relevance rules
- canonical scene-key expectations
- caption-audit statuses
- escalation rules for linked caption problems

## 5. Lock Workflow

The lock workflow should be explicit and reproducible.

1. Run structural verification on benchmark artifacts
2. Finalize retrieval judgments first
3. Run benchmark evaluation
4. Human reviewer performs caption audit during lock review
5. Benchmark maintainer cross-checks each problematic caption against retrieval failures or measurable metric noise in the current run
6. If linked, default to a targeted rerun over affected asset/query pairs after `fix_in_place`
7. Fall back to a full evaluation rerun only when the change affects shared evaluation semantics, broad caption-generation behavior, or identifier handling
8. Resolve all linked benchmark issues
9. Benchmark maintainer performs the single final sign-off before the set is tagged locked

## 6. Structural Verification and Acceptance Flow

Structural verification is a hard precondition. Evaluation must not start until structural verification passes.

### 6.1 Structural verification preconditions
Before evaluation starts, the benchmark must pass all of the following:
- `queries.json` schema validation
- `asset_manifest.json` schema validation
- `audit_log.json` schema validation
- canonical scene-key format enforcement
- rejection of legacy numeric scene IDs in judged scene data
- validation that every `judgment_policy` reference points to an existing doc path and declared version

This order is intentional: if bad identifiers reach the evaluation step, failures become harder to attribute.

### 6.2 audit_log.json enforcement point
`audit_log.json` must pass schema validation in a pre-lock or CI validation step before the benchmark maintainer can sign off.

### 6.3 Evaluation verification
After structural verification passes:
- run the benchmark normally
- use targeted reruns by default for caption-linked corrections
- require full reruns only when identifier handling or shared evaluation semantics change

### 6.4 Acceptance criteria
Acceptance should be checked in this order:
1. benchmark artifacts are schema-valid
2. the revision declares a valid judgment-policy reference
3. evaluator correctness checks pass, especially canonical scene-key matching
4. no unresolved caption issues remain that are linked to measured failures or metric noise
5. benchmark maintainer sign-off is recorded

Evaluator correctness must be resolved before caption-linked audit conclusions are treated as authoritative.

## 7. Implementation Boundaries

This revision is strictly about benchmark rigor.

### In scope
- canonical scene-key handling in the evaluator
- stricter benchmark-artifact validation
- judgment-policy declaration and versioning
- benchmark caption-audit logging
- targeted rerun decision flow for linked benchmark issues
- maintainer sign-off rules for locking the set

### Explicitly out of scope
- retrieval weights
- embedding-model behavior
- ranking logic
- reranking heuristics
- query preprocessing experiments
- search-side debugging triggered by unrelated smoke-validation metric movement

If smoke validation surfaces a regression that is unrelated to benchmark-hardening changes, the default action is:
- log it
- do not block benchmark lock
- file it as a separate follow-up issue

That prevents retrieval-side flukes from stalling benchmark hardening.

## 8. File-Level Change Boundaries

Expected implementation work should stay focused to:
- `testing/evaluation/evaluate_search.py`
- `testing/evaluation/test_evaluate_search.py`
- `testing/evaluation/queries.json`
- `testing/evaluation/asset_manifest.json` only if schema references or metadata wiring require it
- `testing/evaluation/audit_log.json`
- a validation script or validation-test path for benchmark artifacts
- a rubric doc under `docs/metrics/`

No retrieval-service, caption-generation, embedding, or ranking modules should be modified as part of this revision.

## 9. Test Strategy

Testing should be split into four layers.

### 9.1 Schema and structure tests
Verify that the benchmark rejects:
- malformed `audit_log.json`
- missing required audit fields
- invalid `judgment_policy` references
- legacy numeric scene IDs in judged scene data
- non-canonical scene-key formats

### 9.2 Evaluator correctness tests
Verify that:
- stable scene-key judgments match retrieved stable scene keys correctly
- the evaluator no longer assumes legacy numeric scene identifiers for judged scene relevance
- canonical identifier handling is consistent across per-query and aggregate metrics

### 9.3 Lock-workflow tests
Verify that:
- problematic captions are only escalated when linked to measured failures or metric noise
- targeted reruns are selected by default for affected asset/query pairs
- full reruns are only required when shared evaluation semantics are affected
- maintainer sign-off is blocked when structural validation fails

### 9.4 Smoke validation on the locked benchmark
Run the hardened benchmark path against the locked corpus without changing retrieval behavior.

Success in this step means the benchmark path is trustworthy. It does **not** mean retrieval quality improved.

If this smoke validation surfaces an unrelated retrieval-side regression, log it separately and do not block benchmark lock unless the benchmark-hardening change itself plausibly caused it.

## 10. Success Criteria

This revision is successful when:
- benchmark artifacts are schema-valid before evaluation starts
- judged scene references use one canonical scene-key format end to end
- the evaluator correctly matches judged stable scene keys against retrieved stable scene keys
- the benchmark declares its governing judgment policy explicitly
- caption audits are recorded in a structured artifact
- problematic captions only block acceptance when linked to measured retrieval distortion
- targeted reruns are the default remediation path for linked caption issues
- a single benchmark maintainer sign-off governs final lock acceptance

## 11. Risks and Mitigations

### Risk: Legacy identifier assumptions still hide inside tests or helper paths
**Mitigation:** Add explicit regression tests for stable scene-key matching and reject numeric scene IDs before evaluation begins.

### Risk: Caption audit becomes subjective or inconsistent
**Mitigation:** Keep binary retrieval judgments, define a narrow caption-status rubric, and require benchmark-maintainer linkage to measured failures before escalation.

### Risk: Queries artifact becomes ambiguous during schema evolution
**Mitigation:** Make the top-level `judgment_policy` declaration explicit and move judged entries under a named `queries` array.

### Risk: Unrelated retrieval regressions stall benchmark hardening
**Mitigation:** Treat unrelated smoke-validation regressions as separate issues unless the hardening change itself plausibly caused them.

## 12. Definition of Done

This design is fulfilled when:
- the benchmark policy is documented under `docs/metrics/`
- the benchmark artifacts enforce canonical identifiers and schema validation before evaluation
- the evaluator handles stable scene-key judgments correctly
- caption audits and escalation decisions are captured in `audit_log.json`
- the lock workflow supports targeted reruns by default
- final acceptance is gated by benchmark-maintainer sign-off rather than informal convention

## 13. Recommended Next Step

Write an implementation plan for the benchmark-hardening revision, keeping retrieval logic out of scope and sequencing the work as:
1. artifact schema design
2. structural validation
3. evaluator identifier fix
4. regression tests
5. rubric and audit-log wiring
6. lock-workflow verification
