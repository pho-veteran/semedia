# Evaluation Dataset Quality Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute a full quality audit of the Semedia evaluation benchmark by visually verifying every asset, checking judgment consistency, analyzing coverage, and producing a trust verdict before Phase 8.

**Architecture:** This is a manual review workflow with structured documentation output. The audit reads existing evaluation files (`asset_manifest.json`, `queries.json`, and every file under `testing/evaluation/assets/`), performs direct visual inspection of all media, cross-checks judgments for consistency, analyzes dataset coverage, and writes a findings report with a final recommendation on whether the benchmark is source-of-truth ready.

**Tech Stack:** Direct media inspection (images and videos), JSON dataset files, Markdown documentation, Python for any automated integrity checks

---

## Execution Notes

- This audit is **read-only** until the findings report is complete. No benchmark labels should be changed during the audit.
- Every asset must be visually inspected directly. The audit is incomplete if any asset has not been opened and reviewed.
- Findings and proposed fixes remain separate. The audit documents issues; corrections happen in a follow-up pass if needed.
- The final report goes under `docs/superpowers/specs/` or a location chosen during execution.

## File Structure

### Files read during audit
- `testing/evaluation/asset_manifest.json` — per-asset metadata and benchmark descriptions
- `testing/evaluation/queries.json` — judged queries with relevance annotations
- Every file under `testing/evaluation/assets/` — the actual media to be visually verified
- `docs/metrics/search_quality_history.md` — context on current baseline and evaluation state
- `docs/TASKS.md` and `docs/plan.md` — roadmap context for Phase 8 readiness

### Files produced by audit
- Audit findings report (path TBD during execution, likely `docs/superpowers/specs/2026-05-03-evaluation-dataset-audit-findings.md`)

### Files that may be updated later if corrections are accepted
- `testing/evaluation/asset_manifest.json`
- `testing/evaluation/queries.json`
- Related docs under `docs/metrics/` or `docs/implementations/`

---

## Task 1: Stage A — Integrity Checks

**Files:**
- Read: `testing/evaluation/asset_manifest.json`
- Read: `testing/evaluation/queries.json`
- Read: `testing/evaluation/assets/`

- [ ] **Step 1: Load and parse the manifest file**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

manifest_file = Path('testing/evaluation/asset_manifest.json')
manifest = json.loads(manifest_file.read_text())
print(f'Manifest loaded: {len(manifest)} entries')
for item in manifest[:3]:
    print(f\"  {item['asset_id']}: {item['filename']}\")
"
```

Expected: Manifest parses cleanly and prints the first 3 asset entries.

- [ ] **Step 2: Load and parse the queries file**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

queries_file = Path('testing/evaluation/queries.json')
queries = json.loads(queries_file.read_text())
print(f'Queries loaded: {len(queries)} entries')
judged = [q for q in queries if q.get('judged')]
print(f'Judged queries: {len(judged)}')
"
```

Expected: Queries parse cleanly and print the total and judged counts.

- [ ] **Step 3: Verify every manifest filename exists in assets directory**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

manifest = json.loads(Path('testing/evaluation/asset_manifest.json').read_text())
assets_dir = Path('testing/evaluation/assets')

missing = []
for item in manifest:
    if not (assets_dir / item['filename']).exists():
        missing.append(item['filename'])

if missing:
    print(f'FAIL: {len(missing)} files missing from assets/')
    for f in missing:
        print(f'  - {f}')
else:
    print(f'PASS: All {len(manifest)} manifest files exist in assets/')
"
```

Expected: PASS with all files present.

- [ ] **Step 4: Verify asset IDs and query IDs are unique**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

manifest = json.loads(Path('testing/evaluation/asset_manifest.json').read_text())
queries = json.loads(Path('testing/evaluation/queries.json').read_text())

asset_ids = [item['asset_id'] for item in manifest]
query_ids = [q['query_id'] for q in queries]

if len(asset_ids) != len(set(asset_ids)):
    print('FAIL: Duplicate asset_id values found')
elif len(query_ids) != len(set(query_ids)):
    print('FAIL: Duplicate query_id values found')
else:
    print(f'PASS: {len(asset_ids)} unique asset IDs, {len(query_ids)} unique query IDs')
"
```

Expected: PASS with unique IDs.

- [ ] **Step 5: Verify media type labels match file extensions**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

manifest = json.loads(Path('testing/evaluation/asset_manifest.json').read_text())
assets_dir = Path('testing/evaluation/assets')

mismatches = []
for item in manifest:
    file_path = assets_dir / item['filename']
    ext = file_path.suffix.lower()
    media_type = item['media_type']
    
    if media_type == 'image' and ext not in {'.jpg', '.jpeg', '.png'}:
        mismatches.append(f\"{item['asset_id']}: labeled image but ext={ext}\")
    elif media_type == 'video' and ext not in {'.mp4', '.webm'}:
        mismatches.append(f\"{item['asset_id']}: labeled video but ext={ext}\")

if mismatches:
    print(f'FAIL: {len(mismatches)} media type mismatches')
    for m in mismatches:
        print(f'  - {m}')
else:
    print(f'PASS: All {len(manifest)} media types match file extensions')
"
```

Expected: PASS with no mismatches.

- [ ] **Step 6: Document Stage A findings**

Create a working notes file (e.g., `audit-working-notes.md`) and record:

```md
## Stage A — Integrity Checks

- Manifest entries: <count>
- Query entries: <count>
- Judged queries: <count>
- File existence: PASS/FAIL
- ID uniqueness: PASS/FAIL
- Media type alignment: PASS/FAIL

Issues found:
- <list any failures or warnings>
```

---

## Task 2: Stage B — Visual Verification of Every Asset

**Files:**
- Read: `testing/evaluation/asset_manifest.json`
- Read: Every file under `testing/evaluation/assets/`

- [ ] **Step 1: Generate the asset review checklist**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

manifest = json.loads(Path('testing/evaluation/asset_manifest.json').read_text())

print('# Asset Visual Verification Checklist')
print()
for item in manifest:
    print(f\"## {item['asset_id']}")
    print(f\"- Filename: {item['filename']}\")
    print(f\"- Media type: {item['media_type']}\")
    print(f\"- Description: {item['description']}\")
    print(f\"- Notes: {item['notes']}\")
    print(f\"- Status: [ ] verified / [ ] wording issues / [ ] ambiguity / [ ] mismatch\")
    print(f\"- Visual findings:\")
    print()
" > audit-asset-checklist.md
```

Expected: `audit-asset-checklist.md` created with one section per asset.

- [ ] **Step 2: Open and inspect the first image asset**

Open `testing/evaluation/assets/<first-image-filename>` in an image viewer.

Compare the visible content against:
- The manifest `description`
- The manifest `notes`

Record in `audit-asset-checklist.md`:
- Whether the subject/scene matches the description
- Whether the description is accurate, overstated, vague, or misleading
- Status: `verified`, `verified with wording issues`, `judgment ambiguity`, or `mismatch`

- [ ] **Step 3: Repeat Step 2 for every remaining image asset**

For each image in the manifest:
1. Open the file
2. Compare visible content against manifest text
3. Record status and findings in the checklist

This step is complete only when every image has been visually checked.

- [ ] **Step 4: Open and inspect the first video asset**

Open `testing/evaluation/assets/<first-video-filename>` in a video player.

Watch the video and verify:
- The visible subject and scene match the description
- Any motion or action claims in the notes are accurate
- The description does not overclaim what is actually visible

Record status and findings in `audit-asset-checklist.md`.

- [ ] **Step 5: Repeat Step 4 for every remaining video asset**

For each video in the manifest:
1. Open and watch the file
2. Compare visible content and motion against manifest text
3. Record status and findings in the checklist

This step is complete only when every video has been visually checked.

- [ ] **Step 6: Summarize Stage B findings**

Count the status distribution:

```bash
cd Semedia
grep -c "Status: \[x\] verified" audit-asset-checklist.md
grep -c "Status: \[x\] wording issues" audit-asset-checklist.md
grep -c "Status: \[x\] ambiguity" audit-asset-checklist.md
grep -c "Status: \[x\] mismatch" audit-asset-checklist.md
```

Add to `audit-working-notes.md`:

```md
## Stage B — Visual Verification

- Total assets reviewed: <count>
- Verified: <count>
- Verified with wording issues: <count>
- Judgment ambiguity: <count>
- Mismatch: <count>

Notable issues:
- <list any mismatches or repeated wording problems>
```

---

## Task 3: Stage C — Judgment and Policy Review

**Files:**
- Read: `testing/evaluation/queries.json`
- Read: `audit-asset-checklist.md` (from Stage B)

- [ ] **Step 1: Build asset-to-query linkage map**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

queries = json.loads(Path('testing/evaluation/queries.json').read_text())

# Build reverse index: media_id -> list of queries
positive_map = {}
for q in queries:
    for mid in q.get('relevant_media_ids', []):
        positive_map.setdefault(mid, []).append(q['query_id'])

print('Asset -> Positive Queries Map')
for mid in sorted(positive_map.keys())[:10]:
    print(f'  media_id {mid}: {positive_map[mid]}')
" > audit-query-linkage.txt
```

Expected: `audit-query-linkage.txt` shows which queries link to which assets.

- [ ] **Step 2: Review positive queries for the first asset**

Pick the first asset from the manifest. Look up its linked positive queries in `queries.json`.

For each linked query:
- Confirm the asset really supports the query text
- Check whether the query notes explain the relevance rule clearly
- Flag if the judgment seems inconsistent with similar queries

Record findings in `audit-working-notes.md` under a new section:

```md
## Stage C — Judgment Review

### Asset: <asset_id>
- Linked positive queries: <list>
- Judgment consistency: PASS/FAIL
- Issues: <describe any inconsistencies>
```

- [ ] **Step 3: Repeat Step 2 for every asset with positive queries**

For each asset:
1. Look up linked positive queries
2. Confirm the asset supports each query
3. Check judgment consistency
4. Record findings

This step is complete when every asset with positive queries has been reviewed.

- [ ] **Step 4: Review negative and near-miss queries**

Filter queries where `relevant_media_ids` and `relevant_scene_ids` are both empty.

For each negative query:
- Confirm the query text is genuinely unsupported by the corpus
- Check whether near-miss queries are rejected for a consistent reason
- Flag if negative logic is inconsistent across similar queries

Record findings:

```md
### Negative Queries
- Total negative queries: <count>
- Near-miss queries: <count>
- Consistency: PASS/FAIL
- Issues: <describe any inconsistent negative logic>
```

- [ ] **Step 5: Check for repeated judgment patterns**

Look for query families with similar wording (e.g., "red car", "blue car", "green car").

Verify:
- Color constraints are applied consistently
- Setting constraints (indoor/outdoor, day/night) are applied consistently
- Action constraints (running, sitting, flying) are applied consistently

Record findings:

```md
### Judgment Pattern Consistency
- Color queries: PASS/FAIL
- Setting queries: PASS/FAIL
- Action queries: PASS/FAIL
- Issues: <describe any inconsistent patterns>
```

- [ ] **Step 6: Summarize Stage C findings**

Add to `audit-working-notes.md`:

```md
## Stage C Summary

- Assets with positive queries reviewed: <count>
- Judgment consistency issues: <count>
- Negative query issues: <count>
- Pattern consistency issues: <count>

Critical findings:
- <list any judgment problems that would distort metrics>
```

---

## Task 4: Stage D — Coverage Analysis

**Files:**
- Read: `testing/evaluation/queries.json`
- Read: `testing/evaluation/asset_manifest.json`

- [ ] **Step 1: Compute query type distribution**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

queries = json.loads(Path('testing/evaluation/queries.json').read_text())
judged = [q for q in queries if q.get('judged')]

by_type = {}
for q in judged:
    qtype = q.get('query_type', 'unknown')
    by_type[qtype] = by_type.get(qtype, 0) + 1

print('Query Type Distribution:')
for qtype, count in sorted(by_type.items()):
    print(f'  {qtype}: {count}')
"
```

Expected: Counts for object, action, scene, and any other types.

- [ ] **Step 2: Compute modality and difficulty distribution**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

queries = json.loads(Path('testing/evaluation/queries.json').read_text())
judged = [q for q in queries if q.get('judged')]

by_modality = {}
by_difficulty = {}
for q in judged:
    mod = q.get('media_type_target', 'unknown')
    diff = q.get('difficulty', 'unknown')
    by_modality[mod] = by_modality.get(mod, 0) + 1
    by_difficulty[diff] = by_difficulty.get(diff, 0) + 1

print('Modality Distribution:')
for mod, count in sorted(by_modality.items()):
    print(f'  {mod}: {count}')

print('Difficulty Distribution:')
for diff, count in sorted(by_difficulty.items()):
    print(f'  {diff}: {count}')
"
```

Expected: Counts for image/video/mixed and easy/medium/hard.

- [ ] **Step 3: Compute positive/negative/near-miss distribution**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

queries = json.loads(Path('testing/evaluation/queries.json').read_text())
judged = [q for q in queries if q.get('judged')]

positives = [q for q in judged if q.get('relevant_media_ids') or q.get('relevant_scene_ids')]
negatives = [q for q in judged if not q.get('relevant_media_ids') and not q.get('relevant_scene_ids')]
near_miss = [q for q in judged if 'near-miss' in q.get('tags', [])]

print(f'Positive queries: {len(positives)}')
print(f'Negative queries: {len(negatives)}')
print(f'Near-miss queries: {len(near_miss)}')
"
```

Expected: Counts for each polarity category.

- [ ] **Step 4: Check for overrepresented assets**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

queries = json.loads(Path('testing/evaluation/queries.json').read_text())

media_counts = {}
for q in queries:
    for mid in q.get('relevant_media_ids', []):
        media_counts[mid] = media_counts.get(mid, 0) + 1

print('Top 10 Most-Referenced Assets:')
for mid, count in sorted(media_counts.items(), key=lambda x: -x[1])[:10]:
    print(f'  media_id {mid}: {count} queries')
"
```

Expected: List of most-referenced assets. Flag if any single asset dominates.

- [ ] **Step 5: Evaluate media-level vs scene-level judgment coverage**

Run:

```bash
cd Semedia
python -c "
import json
from pathlib import Path

queries = json.loads(Path('testing/evaluation/queries.json').read_text())

media_only = [q for q in queries if q.get('relevant_media_ids') and not q.get('relevant_scene_ids')]
scene_level = [q for q in queries if q.get('relevant_scene_ids')]

print(f'Media-level judgments: {len(media_only)}')
print(f'Scene-level judgments: {len(scene_level)}')
"
```

Expected: Counts showing whether scene-level judgments exist for video queries.

- [ ] **Step 6: Summarize Stage D findings**

Add to `audit-working-notes.md`:

```md
## Stage D — Coverage Analysis

- Query type balance: <object/action/scene counts>
- Modality balance: <image/video/mixed counts>
- Difficulty balance: <easy/medium/hard counts>
- Polarity balance: <positive/negative/near-miss counts>
- Overrepresented assets: <list if any>
- Media-level vs scene-level: <counts>

Coverage gaps:
- <list any underrepresented query families>
- <note if video judgments are too coarse for Phase 8>
```

---

## Task 5: Stage E — Fitness-for-Use Verdict

**Files:**
- Read: `audit-working-notes.md` (from Stages A-D)
- Create: Final audit findings report

- [ ] **Step 1: Review all working notes and classify issues by severity**

Read through `audit-working-notes.md` and classify each issue:

- **Minor wording issues**: sloppy or unclear descriptions that don't affect core judgment
- **Judgment ambiguity**: relevance depends on interpretation and notes don't clarify
- **Material mismatch**: visible media and benchmark text materially disagree
- **Inconsistent standards**: similar queries judged by different rules

Record the classification:

```md
## Issue Classification

### Minor wording issues (<count>)
- <list>

### Judgment ambiguity (<count>)
- <list>

### Material mismatches (<count>)
- <list>

### Inconsistent standards (<count>)
- <list>
```

- [ ] **Step 2: Apply escalation rules and determine verdict**

Use these rules:

- A small number of wording problems → `usable with caveats`
- Repeated ambiguity across a query family → more serious than isolated wording
- Material mismatches or inconsistent standards → blocks `source-of-truth ready`
- Video judgments too coarse for Phase 8 → cannot be `source-of-truth ready` without caveats

Choose one verdict:
- `source-of-truth ready`
- `usable with caveats`
- `not reliable enough yet`

Record:

```md
## Final Verdict

**Status:** <verdict>

**Reasoning:**
- <explain why this verdict was chosen>
- <reference specific issue counts and patterns>
```

- [ ] **Step 3: Write the prioritized correction list**

If the verdict is not `source-of-truth ready`, list corrections in priority order:

```md
## Recommended Corrections (Priority Order)

1. **Fix material mismatches**
   - <list specific assets and what needs correction>

2. **Resolve inconsistent judgment standards**
   - <list specific query families and the rule to apply>

3. **Clarify judgment ambiguity**
   - <list specific queries that need clearer notes>

4. **Fix minor wording issues**
   - <list specific descriptions to improve>
```

- [ ] **Step 4: Write the final recommendation**

Add:

```md
## Recommendation

**Should Semedia proceed to Phase 8?**

- [ ] Proceed directly to Phase 8
- [ ] Proceed to Phase 8 with documented caveats
- [ ] Pause and fix the evaluation dataset first

**Rationale:**
- <explain the recommendation based on the verdict and issue severity>
- <if caveats, list what they are>
- <if fixes needed, estimate scope>
```

- [ ] **Step 5: Compile the final audit findings report**

Create the final report file (e.g., `docs/superpowers/specs/2026-05-03-evaluation-dataset-audit-findings.md`) with this structure:

```md
# Evaluation Dataset Quality Audit — Findings

**Date:** 2026-05-03
**Auditor:** <name or "Claude Code">
**Scope:** Full quality audit of Semedia evaluation benchmark before Phase 8

## Executive Summary

- Assets reviewed: <count>
- Queries reviewed: <count>
- Verdict: <verdict>
- Recommendation: <proceed/caveat/pause>

## Stage A — Integrity Checks

<copy from working notes>

## Stage B — Visual Verification

<copy from working notes and asset checklist>

## Stage C — Judgment and Policy Review

<copy from working notes>

## Stage D — Coverage Analysis

<copy from working notes>

## Stage E — Fitness-for-Use Verdict

<copy verdict, reasoning, corrections, and recommendation>

## Appendix: Per-Asset Findings

<copy relevant sections from audit-asset-checklist.md>
```

- [ ] **Step 6: Review the final report for completeness**

Check:
- [ ] Every mandatory checklist item from the spec is addressed
- [ ] All assets have been visually verified
- [ ] All queries have been reviewed
- [ ] The verdict is clear and justified
- [ ] The recommendation is actionable

Expected: Final report is complete and ready for user review.

---

## Spec Coverage Check

- Verify corpus integrity: **Task 1**
- Visual verification of every asset: **Task 2**
- Judgment quality and consistency: **Task 3**
- Coverage analysis: **Task 4**
- Fitness-for-use verdict: **Task 5**
- Final recommendation on Phase 8: **Task 5**
- Written audit report: **Task 5**

## Self-Review Notes

- No placeholders remain for commands or expected outputs
- Every asset must be visually checked (enforced in Task 2)
- Findings and corrections are kept separate (enforced in Task 5)
- The plan produces a complete audit report with a clear verdict
- The audit is read-only until the findings report is complete
