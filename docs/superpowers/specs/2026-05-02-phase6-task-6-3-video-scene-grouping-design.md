# Phase 6.3 Video Scene Grouping Design

**Date:** 2026-05-02  
**Status:** Proposed

## Summary

Phase 6.3 will reduce duplicate-heavy search result pages by grouping related `video_scene` results from the same video under a single parent result. The UI will keep image results unchanged, show the best-matching scene first for each video, include a small preview strip for the next one or two scenes, and allow the user to expand the group inline to reveal all remaining matching scenes.

## Problem

The current search page renders every result independently. When several scenes from the same video rank highly, they occupy multiple grid slots and push other useful results farther down the page. This makes the result set feel repetitive even when the underlying search quality is good.

## Goals

1. Reduce visual clutter when multiple scenes from the same video match.
2. Preserve access to strong secondary scenes from the same video.
3. Keep the highest-value scene visible without requiring expansion.
4. Keep image results and single-scene results simple.
5. Make scene expansion feel like part of the existing result grid rather than a separate view.

## Non-Goals

1. No backend schema or API changes.
2. No reranking changes.
3. No metadata sorting changes from Phase 6.4.
4. No redesign of image result cards.
5. No cross-video deduplication beyond grouping scenes by `media_id`.

## Proposed Approach

### Result grouping

`SearchPage.tsx` will group only results where `result_type === 'video_scene'` by `media_id` after filtering and sorting are applied. Images will remain standalone results.

Within each grouped video result:
- scenes stay ordered by descending `score`
- the highest-scoring scene becomes the lead scene
- the next one or two scenes become collapsed previews
- any remaining scenes stay hidden until expansion

Single-scene video matches will render as a grouped video result with no expansion control.

### UI structure

Add a dedicated grouped-result component, likely `frontend/src/components/SearchResultGroup.tsx`.

Each grouped result will contain:
1. **Lead scene card** — visually aligned with the current `SearchResultCard`, preserving score, timestamp, ranking badges, explanation summary, and caption.
2. **Preview strip** — compact previews for the next one or two scenes, each showing thumbnail and time range.
3. **Expansion control** — a button labeled like `Show 3 more scenes` or `Hide extra scenes`.
4. **Expanded scenes area** — inline list or grid of the remaining scenes using a compact scene item layout.

The lead card remains the primary visual anchor. The preview strip gives quick context without flooding the page.

### Interaction behavior

- Clicking the lead scene opens that exact video at the lead scene `start_time`.
- Clicking a preview scene opens that exact preview scene.
- Clicking an expanded scene opens that exact expanded scene.
- Expansion is local to each grouped video result.
- Expansion state resets when a new search result set is loaded.

### Result ordering

The grouped video result should occupy the position of its best scene in the already-sorted search results. This preserves overall relevance ordering while reducing repeated cards for the same video.

Example:
- If scenes A1, A2, and A3 from video A appear among the sorted results, the grouped video A result is inserted at the position of A1.
- A2 and A3 are removed from the top-level rendered result list and appear inside the grouped result instead.

## Component boundaries

### `SearchPage.tsx`

Responsibilities:
- keep existing search, filter, and sort behavior
- transform the filtered/sorted flat result list into renderable grouped entries
- reset focus/expansion state on new results if needed
- render grouped video results alongside standalone image results

### `SearchResultGroup.tsx`

Responsibilities:
- render one grouped video result
- manage expand/collapse state for that result
- render lead scene, preview strip, and expanded scenes
- call `onOpenMedia(mediaId, startTime)` for the selected scene

### `SearchResultCard.tsx`

Responsibilities:
- remain reusable for standalone image results
- optionally remain reusable for the lead scene if that can be done cleanly without forcing awkward props

If adapting `SearchResultCard` makes the API messy, the grouped component may duplicate only the minimal presentational markup needed for the lead scene.

## Data flow

1. API returns a flat `SearchResult[]` as it does today.
2. `SearchPage.tsx` applies the current type and score filters.
3. `SearchPage.tsx` applies the current client-side sort.
4. `SearchPage.tsx` converts the flat list into render entries:
   - standalone image entries
   - grouped video entries keyed by `media_id`
5. Render logic maps those entries to either `SearchResultCard` or `SearchResultGroup`.
6. User actions on lead, preview, or expanded scenes call `onOpenMedia()` with the selected scene timestamp.

## Accessibility and keyboard behavior

- Expansion control must be a real button.
- Preview items and expanded scene items must be keyboard reachable.
- Enter/Space on a focused preview or expanded scene should open the selected scene.
- Existing arrow-key focus behavior on the page may continue to operate at the top-level rendered entry level for Phase 6.3.

This keeps the first version scoped. If group-internal arrow navigation becomes necessary, that can be handled in a later refinement.

## Error handling and edge cases

1. **No thumbnail for a scene:** fall back to the existing muted placeholder behavior.
2. **Video with only one matching scene:** render no preview strip and no expansion button.
3. **Video with two or three matching scenes:** show previews only for the additional scenes; expansion button appears only if more scenes remain hidden.
4. **Mixed results:** image results continue rendering exactly as before.
5. **Repeated searches or filter changes:** expansion state should not leak across result sets.

## Testing strategy

Add or update frontend tests to cover:

1. grouping multiple `video_scene` results with the same `media_id`
2. preserving standalone rendering for image results
3. keeping the best-scoring scene as the lead scene
4. showing the preview strip for the next one or two scenes
5. showing `Show N more scenes` only when hidden scenes remain
6. expanding inline to reveal the rest of the scenes
7. opening the correct `start_time` when the user clicks a preview or expanded scene
8. leaving single-scene videos unexpanded

Primary test targets:
- `frontend/src/pages/SearchPage.test.tsx`
- `frontend/src/components/SearchResultCard.test.tsx` if existing behavior needs adjustment
- new grouped-result component tests if a dedicated component is added

## Implementation notes

Recommended implementation sequence:
1. Add a small grouping helper and tests for grouped render entries.
2. Create the grouped-result component with a lead scene and preview strip.
3. Wire grouped entries into `SearchPage.tsx`.
4. Add expansion behavior and scene click handling.
5. Verify that image results and current ranking badges still render correctly.

## Success criteria

Phase 6.3 is complete when:
- repeated scenes from the same video no longer flood the top-level results grid
- the best scene remains immediately visible
- users can inspect additional scenes inline without leaving the page
- clicking any visible scene opens the correct video timestamp
- existing image-result behavior remains intact
