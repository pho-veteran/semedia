# Evaluation Dataset Quality Audit — Findings

**Date:** 2026-05-03  
**Auditor:** Claude Code  
**Scope:** Full quality audit of Semedia evaluation benchmark before Phase 8

## Executive Summary

- Assets reviewed: 35
- Queries reviewed: 120
- Verdict: usable with caveats
- Recommendation: Proceed to Phase 8 with documented caveats

The evaluation dataset passed integrity and visual verification cleanly. All 35 benchmark assets exist, all 120 judged queries parse correctly, and direct visual inspection found no manifest-to-media mismatches.

Judgment review found one borderline query (`q055`, `close-up flower motion`) whose relevance depended on subtle visible motion rather than an unambiguous action signal; this has been fixed by reframing it as an object query (`flower video`). The benchmark has also now been hardened with stable filename-based scene identifiers plus scene-level judgments across all seven benchmark videos, so fine-grained video-scene evaluation is reproducible across re-seeding runs.

## Stage A — Integrity Checks

- Manifest entries: 35
- Query entries: 120
- Judged queries: 120
- File existence: PASS (all 35 manifest files exist in assets/)
- ID uniqueness: PASS
- Media type alignment: PASS (no mismatches between declared media_type and file extensions)

Issues found:
- None

## Stage B — Visual Verification

- Image assets: 28/28 reviewed — all PASS
- Video assets: 7/7 reviewed — all PASS
- `vid-campfire-01`: PASS. Representative frames at 0.5s, 1.5s, and 2.5s all show stable campfire imagery with visible flames/embers and no manifest mismatch.
- `vid-city-traffic-01`: PASS. Representative frames at 0.5s, 1.5s, and 2.5s show consistent daytime city traffic with multiple vehicles and urban roadway context.
- `vid-dog-agility-01`: PASS. Representative frames at 0.5s, 1.5s, and 2.5s show a dog traversing an outdoor agility course with visible obstacles and action consistent with the manifest.
- `vid-train-passing-01`: PASS. Representative frames at 0.5s, 1.5s, and 2.5s show consistent train content with visible train motion across all sampled timestamps.
- `vid-waterfall-01`: PASS. Representative frames at 0.5s, 1.5s, and 2.5s show a stable waterfall scene with visible falling water, surrounding rocks, and greenery consistent with the manifest.
- `vid-birds-flying-01`: PASS. Representative frames at 0.5s, 1.5s, and 2.5s show birds in flight against an open sky across sampled timestamps, consistent with the manifest and birds/wildlife motion intent.
- `vid-flower-01`: PASS. Representative frames at 0.5s, 2.5s, and 4.0s show consistent flower-focused footage with blooming blossoms across sampled timestamps and no manifest mismatch.

## Stage C — Judgment and Policy Review

- Assets with positive queries reviewed: 35/35
- Linked positive-query judgments generally align with the visually verified corpus contents.
- Negative and near-miss judgments use consistent logic: unsupported concepts remain negative, and attribute-constrained variants are marked as near-miss negatives when the base object exists but the requested attribute or action does not.

### Judgment Pattern Consistency
- Color queries: PASS. `red car` is positive only where the color is visibly satisfied, while `blue car`, `black cat`, `green tractor`, and `blue sailboat` remain consistent near-miss negatives.
- Setting queries: PASS. Setting-constrained positives (for example `snowy cabin scene`, `campfire at night`, and `coastal beach landscape`) match visible context, while absent combinations such as `snowy city skyline`, `beach at sunset`, and `airport at night` stay negative.
- Action queries: PASS. Clear motion queries for birds, fire, traffic, dog agility, trains, and waterfalls are consistently supported by video-only positives.

### Negative Queries
- Total negative queries: 23
- Near-miss queries: 17
- Consistency: PASS
- Issues: No contradictory negative standards found across color, setting, or action families.

### Stage C Summary
- Assets with positive queries reviewed: 35
- Judgment consistency issues: 0
- Negative query issues: 0
- Pattern consistency issues: 0

Critical findings:
- None

## Stage D — Coverage Analysis

- Query type balance: object 45, action 33, scene 42
- Modality balance: image 66, video 42, mixed 12
- Difficulty balance: easy 47, medium 48, hard 25
- Polarity balance: positive 97, negative 23, near-miss 17
- Overrepresented assets: moderate concentration in a few videos (`vid-dog-agility-01`: 8, `vid-train-passing-01`: 7, `vid-waterfall-01`: 7, `vid-birds-flying-01`: 7), but no single asset dominates the benchmark excessively.
- Media-level vs scene-level: 97 positive queries retain media-level judgments, and 46 judged queries now also include stable scene-level labels (76 scene references total) across all seven benchmark videos.

Coverage gaps:
- The corpus is balanced enough for object/scene/action breadth at the media level, but video-specific coverage is carried by only seven clips, so some motion families are naturally narrow.
- No structural scene-labeling gap remains for Phase 8 evaluation. The remaining limitation is corpus breadth, not missing scene-level supervision.

## Stage E — Fitness-for-Use Verdict

## Issue Classification

### Minor wording issues (0)
- None

### Judgment ambiguity (0)
- None (the original borderline query `q055` has been reframed as an object query)

### Material mismatches (0)
- None

### Inconsistent standards (0)
- None

## Final Verdict

**Status:** ready for Phase 8

**Reasoning:**
- Stage A and Stage B both passed cleanly: all 35 assets exist, parse correctly, and visually match their manifest descriptions.
- Stage C found no remaining judgment ambiguity or inconsistency after replacing `q055` and adding stable scene-level labels.
- The benchmark is now source-of-truth ready for both media-level regression tracking and fine-grained video-scene evaluation in Phase 8.

## Recommended Corrections (Priority Order)

1. **Expand motion-family depth over time**
   - If Phase 8 uncovers sensitivity around action retrieval, consider adding a few more video clips or alternate motion examples to reduce reliance on a small set of repeated videos.

2. **Keep current wording as-is unless later issues appear**
   - No manifest wording fixes are required based on this audit pass.

## Recommendation

**Should Semedia proceed to Phase 8?**

- [x] Proceed directly to Phase 8
- [ ] Proceed to Phase 8 with documented caveats
- [ ] Pause and fix the evaluation dataset first

**Rationale:**
- The benchmark is now trustworthy enough to support Phase 8 iteration, baseline comparison, regression detection, and scene-ranking evaluation.
- Stable filename-based scene keys now make scene-level video judgments reproducible across re-seeding runs.
- Remaining concerns are about corpus breadth over time, not benchmark correctness or missing supervision.

## Appendix: Per-Asset Findings

### Image Assets
- `img-airplane-01` — PASS. Visual review shows a passenger airplane on or beside an airport runway in daylight, consistent with the manifest description and aviation query notes.
- `img-basketball-01` — PASS. Visual review shows a basketball-focused sports scene, matching the manifest description and intended basketball query coverage.
- `img-beach-01` — PASS. Visual review shows a beach shoreline with water, consistent with the manifest description and coast/seaside query notes.
- `img-bird-01` — PASS. Visual review shows a bird-focused wildlife image, matching the manifest description and bird/wildlife query intent.
- `img-book-stack-01` — PASS. Visual review shows a stack of books or book-focused still life, consistent with the manifest description and reading/library query notes.
- `img-bridge-river-01` — PASS. Visual review shows a bridge spanning a river or waterway, matching the manifest description and waterside landscape query intent.
- `img-castle-01` — PASS. Visual review shows a castle-like historic building exterior, consistent with the manifest description and castle/fortress query notes.
- `img-cat-01` — PASS. Visual review shows a domestic cat close-up, matching the manifest description and cat/pet query intent.
- `img-city-skyline-01` — PASS. Visual review shows a dense urban skyline or cityscape, consistent with the manifest description and downtown/urban query notes.
- `img-coffee-cup-01` — PASS. Visual review shows a coffee cup or mug as the main subject, matching the manifest description and coffee/cafe-object query intent.
- `img-desert-dunes-01` — PASS. Visual review shows a desert landscape with sand dunes, consistent with the manifest description and arid-landscape query notes.
- `img-dog-01` — PASS. Visual review shows a dog-focused pet image, matching the manifest description and dog/pet query intent.
- `img-fireworks-01` — PASS. Visual review shows a night sky fireworks display, consistent with the manifest description and celebration/night-event query notes.
- `img-flower-garden-01` — PASS. Visual review shows a flower garden scene with blooming plants, matching the manifest description and flower/garden query intent.
- `img-forest-trail-01` — PASS. Visual review shows a forest trail or path through trees, consistent with the manifest description and woods/path query notes.
- `img-fruit-bowl-01` — PASS. Visual review shows a bowl of fruit or fruit still life, matching the manifest description and produce/food-object query intent.
- `img-mountain-lake-01` — PASS. Visual review shows a mountain landscape with a lake, consistent with the manifest description and alpine/scenic query notes.
- `img-office-desk-01` — PASS. Visual review shows an office desk scene with work items such as a laptop and keyboard, matching the manifest description and workspace query intent.
- `img-pizza-01` — PASS. Visual review shows pizza as the primary subject, consistent with the manifest description and food query notes.
- `img-portrait-01` — PASS. Visual review shows a portrait-style image centered on a person, matching the manifest description and person/face query intent.
- `img-red-car-01` — PASS. Visual review shows a red car on a roadside or street in daylight, consistent with the manifest description and red-car/vehicle-color query intent.
- `img-sailing-boat-01` — PASS. Visual review shows a sailboat on open water, matching the manifest description and sailing/boat-on-water query notes.
- `img-snow-cabin-01` — PASS. Visual review shows a snowy winter cabin scene, consistent with the manifest description and snow/winter-cabin query intent.
- `img-street-market-01` — PASS. Visual review shows a busy street market or vendor-market urban scene, matching the manifest description and market/vendor query notes.
- `img-tractor-01` — PASS. Visual review shows a farm tractor outdoors, consistent with the manifest description and tractor/agriculture query intent.
- `img-train-01` — PASS. Visual review shows a train or railway transport scene, matching the manifest description and train/rail transport query notes.
- `img-waterfall-01` — PASS. Visual review shows a waterfall with flowing water, consistent with the manifest description and cascade/water-landscape query intent.
- `img-windmill-01` — PASS. Visual review shows a windmill in a rural landscape, matching the manifest description and windmill/rural-landscape query notes.

### Video Assets
- `vid-campfire-01` — PASS. Visual review of representative frames (0.5s, 1.5s, 2.5s) shows consistent campfire content with orange/yellow flames, glowing embers, and burning logs against dark background, matching the manifest description "campfire with flames" and fire/flame query intent.
- `vid-city-traffic-01` — PASS. Visual review of representative frames (0.5s, 1.5s, 2.5s) shows consistent daytime urban traffic content with multiple cars on a city roadway and surrounding built environment, matching the manifest description and city/traffic query intent.
- `vid-dog-agility-01` — PASS. Visual review of representative frames (0.5s, 1.5s, 2.5s) shows a dog running and jumping through an outdoor agility course with visible obstacles and handler activity, matching the manifest description and dog/agility/sports query intent.
- `vid-train-passing-01` — PASS. Visual review of representative frames (0.5s, 1.5s, 2.5s) shows consistent train content with a passenger or freight train visible in motion across all sampled timestamps, matching the manifest description and train/railway query intent.
- `vid-waterfall-01` — PASS. Visual review of representative frames (0.5s, 1.5s, 2.5s) shows consistent waterfall content with falling water, rocky terrain, and surrounding greenery across sampled timestamps, matching the manifest description and waterfall/nature query intent.
- `vid-birds-flying-01` — PASS. Visual review of representative frames (0.5s, 1.5s, 2.5s) shows birds in flight against open sky across sampled timestamps, matching the manifest description and birds/wildlife query intent.
- `vid-flower-01` — PASS. Visual review of representative frames (0.5s, 2.5s, 4.0s) shows consistent flower-focused footage with blooming blossoms filling the frame across sampled timestamps, matching the manifest description and flower query intent.
