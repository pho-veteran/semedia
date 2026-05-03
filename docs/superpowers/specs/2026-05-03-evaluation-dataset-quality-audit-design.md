# Evaluation Dataset Quality Audit

**Date:** 2026-05-03  
**Status:** Approved design  
**Scope:** Audit the overall quality of the locked evaluation datasets before Phase 8 so the benchmark can be trusted as the source of truth for future search-quality work.

## 1. Objectives

This audit will determine whether the Semedia evaluation benchmark is trustworthy enough to guide retrieval and ranking changes, especially the planned Phase 8 candidate-generation work.

### Primary goals
- Verify the actual media content of every evaluation asset directly
- Confirm that human-written benchmark descriptions and notes match the visible media
- Confirm that positive, negative, and near-miss judgments are internally consistent
- Evaluate whether query coverage is broad and balanced enough to support future retrieval work
- Produce a clear verdict on whether the dataset is source-of-truth ready

### Non-goals
- No search or ranking code changes
- No tuning of retrieval behavior
- No silent relabeling during the audit
- No reliance on generated captions as the benchmark authority
- No expansion of the benchmark corpus unless gaps are first identified and documented

## 2. Current State

### Evaluation assets and metadata
- `testing/evaluation/assets/` contains the locked local benchmark corpus
- `testing/evaluation/asset_manifest.json` contains per-asset metadata, benchmark descriptions, and maintenance notes
- `testing/evaluation/queries.json` contains judged queries spanning object, action, scene, mixed, negative, and near-miss coverage

### Existing strengths
- The benchmark is already local and reproducible
- Asset metadata is structured and human-readable
- Query notes explain judgment intent for most cases
- The dataset includes explicit negatives and near-miss negatives rather than positives only
- Evaluation tooling already supports aggregate metrics, grouped summaries, and saved baselines

### Main risks to address
- Human-written benchmark descriptions or notes may overclaim what is actually visible in the media
- Similar queries may not follow one consistent relevance standard
- Negative and near-miss judgments may be unevenly applied across similar assets
- Video judgments may be too media-level to fully support candidate-generation analysis
- Coverage may look broad overall while still underrepresenting specific failure-prone query patterns

## 3. Audit Questions

The audit should answer these questions:

1. Does every asset visually match its benchmark description and notes?
2. Do the linked judgments in `queries.json` follow a consistent standard?
3. Are explicit negatives and near-miss negatives trustworthy and repeatable?
4. Is the dataset balanced enough across query type, modality, difficulty, and polarity to evaluate future changes?
5. Is the benchmark strong enough to serve as the source of truth for Phase 8, or are dataset fixes required first?

## 4. Audit Scope

### 4.1 Corpus integrity
Verify that the benchmark corpus is internally coherent.

Checks:
- Every manifest entry maps to a real asset file
- Filenames are unique
- Asset IDs are unique
- Media type labels match the actual file type
- Manifest descriptions and notes are present and interpretable

### 4.2 Query integrity
Verify that query data is structurally valid and semantically coherent.

Checks:
- Query IDs are unique
- Required fields are consistently populated
- Query taxonomy is used consistently (`query_type`, `media_type_target`, `difficulty`, `tags`)
- Positive, negative, and near-miss queries are clearly distinguishable from each other
- Relevance annotations point to valid benchmark targets

### 4.3 Judgment quality
Verify that the written judgments are correct and repeatable.

Checks:
- Positive queries are genuinely supported by the visible media
- Negative queries are genuinely unsupported by the visible media
- Near-miss negatives are rejected for a clear reason that is consistent with the notes
- Similar assets and similar queries are judged under the same standard
- Benchmark notes explain the relevance rule clearly enough that another reviewer would likely reach the same conclusion

### 4.4 Benchmark usefulness
Verify that the benchmark is useful for measuring future retrieval work.

Checks:
- Coverage across object, action, and scene queries
- Coverage across image, video, and mixed targets
- Coverage across easy, medium, and hard queries
- Coverage across positives, negatives, and near-miss negatives
- Whether any single asset or query family is overrepresented enough to distort interpretation
- Whether media-level judgments are sufficient for upcoming work or likely to hide scene-level ambiguity

## 5. Review Method

The audit will proceed in five stages.

### Stage A — Integrity checks
Perform structural and file-level validation.

Actions:
- Confirm manifest and query files parse cleanly
- Confirm each manifest filename exists in `testing/evaluation/assets/`
- Confirm asset IDs and query IDs are unique
- Confirm referenced relevance IDs are valid and interpretable
- Confirm declared media types align with actual file extensions and formats

### Stage B — Visual verification of every asset
Inspect every benchmark asset directly.

Actions:
- Open every image and verify the visible subject and scene
- Inspect every video and verify the visible subject, scene, and motion claims
- Compare the actual media against the asset manifest `description`
- Compare the actual media against the asset manifest `notes`
- Record whether the written benchmark text is accurate, overstated, vague, or misleading

This is a mandatory part of the audit. The audit is incomplete if any asset has not been visually checked directly.

### Stage C — Judgment and policy review
Cross-check judgments against the verified assets.

Actions:
- For each asset, review its linked positive queries
- Confirm that the asset really supports each claimed positive judgment
- Review linked negative and near-miss queries where the asset is an implicit comparison case
- Check whether wording like color, setting, action, and modality constraints is applied consistently across similar entries
- Flag ambiguous or inconsistent judgment rules

### Stage D — Coverage analysis
Review the benchmark as a whole.

Actions:
- Summarize coverage by query type, modality, difficulty, and polarity
- Identify gaps in query families that matter to current roadmap work
- Identify whether certain assets, categories, or media types dominate too much of the benchmark
- Evaluate whether video judgments are too coarse for candidate-generation evaluation

### Stage E — Fitness-for-use verdict
End the audit with a decision on benchmark trustworthiness.

Possible verdicts:
- `source-of-truth ready`
- `usable with caveats`
- `not reliable enough yet`

The verdict must distinguish between minor wording issues and deeper judgment problems that would distort metric interpretation.

## 6. Mandatory Audit Checklist

Every item below must be completed.

1. **Visual identity check per asset**
   - Confirm the asset is really what the benchmark says it is (dog, cat, person, train, waterfall, office, beach, etc.)
2. **Manifest description check**
   - Confirm each `description` is factually accurate
3. **Manifest notes check**
   - Confirm each `notes` field does not overclaim or mislead
4. **Positive-query check**
   - Confirm linked positive queries are genuinely relevant to the visible media
5. **Negative and near-miss check**
   - Confirm negatives are truly unsupported and near-misses are rejected for a consistent reason
6. **Consistency check**
   - Confirm similar assets and similar query phrasings follow the same relevance standard
7. **Coverage check**
   - Confirm the dataset is broad enough and balanced enough to evaluate future search changes
8. **Phase-8 readiness check**
   - Confirm whether media-level judgments are sufficient for candidate-generation work or whether scene-level gaps would weaken future conclusions

## 7. Decision Rules

Each asset or judgment issue should be classified using one of the following statuses:

- `verified` — the media clearly matches the benchmark text and judgments
- `verified with wording issues` — the core judgment is right, but the written description or note is sloppy, overstated, or unclear
- `judgment ambiguity` — relevance depends on interpretation and the current notes do not make the rule sufficiently explicit
- `mismatch` — the visible media and the benchmark text materially disagree

### Escalation rules
- A small number of wording problems can still support a final verdict of `usable with caveats`
- Repeated ambiguity across a query family is more serious than a single isolated wording problem
- Material mismatches, inconsistent standards, or misleading negative logic should block source-of-truth status
- If video judgments are too coarse to support Phase 8 conclusions, the benchmark cannot be treated as fully ready for that phase without caveats

## 8. Outputs

### Primary output
A written audit report under `docs/superpowers/specs/` that records:
- per-asset findings
- cross-cutting dataset issues
- benchmark coverage observations
- final trust verdict
- prioritized correction list if needed

### Per-asset output
Each asset should receive one of the four statuses:
- `verified`
- `verified with wording issues`
- `judgment ambiguity`
- `mismatch`

### Cross-dataset output
Summaries should include:
- taxonomy consistency
- positive/negative/near-miss judgment quality
- modality and difficulty coverage
- repeated query-pattern quality
- media-level vs scene-level limitations

### Final recommendation
The audit must answer whether Semedia should:
1. proceed directly to Phase 8
2. proceed to Phase 8 with documented benchmark caveats
3. pause and fix the evaluation dataset first

## 9. File and Process Changes

### Files read during audit
- `testing/evaluation/asset_manifest.json`
- `testing/evaluation/queries.json`
- every file under `testing/evaluation/assets/`
- supporting evaluation docs as needed

### Files expected to be produced
- audit spec: `docs/superpowers/specs/2026-05-03-evaluation-dataset-quality-audit-design.md`
- audit findings report: path to be chosen during planning/execution

### Files that may be updated later if issues are accepted
- `testing/evaluation/asset_manifest.json`
- `testing/evaluation/queries.json`
- benchmark-related docs under `docs/metrics/` or `docs/implementations/`

No benchmark labels should be changed during the audit-design phase. Findings and proposed fixes should remain separate.

## 10. Acceptance Criteria

The audit is complete only if all of the following are true:
- Every asset has been visually checked directly
- Every manifest `description` and `notes` pair has been reviewed
- Every query has been reviewed through its linked asset context
- All material mismatches, ambiguities, and wording issues are documented
- The benchmark receives a clear final verdict
- The final report includes a concrete recommendation on whether Phase 8 should proceed immediately or wait for benchmark corrections

## 11. Risks and Mitigations

### Risk: Visual review is time-consuming
**Mitigation:** Treat this as intentional cost. Source-of-truth claims require direct review, not schema-only validation.

### Risk: Similar queries expose inconsistent judgment policy
**Mitigation:** Record the policy explicitly in findings and prefer one consistent interpretation over ad hoc exceptions.

### Risk: Video judgments are too coarse for future retrieval work
**Mitigation:** Call this out directly in the verdict instead of masking it behind aggregate metric coverage.

### Risk: Benchmark quality issues create pressure to fix labels immediately
**Mitigation:** Keep the audit report separate from any follow-up correction pass so findings stay reviewable.

## 12. Definition of Done

This audit design is fulfilled when:
- the full benchmark corpus has been visually reviewed asset by asset
- benchmark descriptions and notes have been checked against actual media content
- query judgments have been checked for consistency and correctness
- dataset coverage has been analyzed at the benchmark level
- a written audit report provides a trust verdict and follow-up recommendation

## 13. Recommended Next Step After This Audit

1. Execute the audit against the full locked benchmark corpus
2. Review the audit findings with the user
3. If needed, correct the benchmark data and rerun the trust check
4. Only then proceed to Phase 8 candidate-generation work using the audited benchmark as the evaluation authority
