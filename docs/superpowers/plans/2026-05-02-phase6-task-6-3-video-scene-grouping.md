# Phase 6.3 Video Scene Grouping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Group related `video_scene` search results by `media_id`, show the best scene first, add a preview strip for the next one or two scenes, and allow inline expansion for the remaining scenes.

**Architecture:** Keep the backend response flat and perform grouping entirely in the frontend after the current filter and sort pipeline. Add one focused utility to convert a flat `SearchResult[]` into renderable entries, then add a dedicated grouped-result component that renders a lead scene, preview strip, and expandable remainder. Leave image results and the existing `SearchResultCard` behavior intact.

**Tech Stack:** React 19, TypeScript, Vitest, Testing Library, Tailwind utility classes, existing Semedia frontend UI primitives

---

## File Structure

### New files
- `frontend/src/utils/searchResults.ts` — groups the filtered/sorted flat `SearchResult[]` into render entries for standalone images and grouped videos.
- `frontend/src/utils/searchResults.test.ts` — unit tests for grouping behavior and ordering.
- `frontend/src/components/SearchResultGroup.tsx` — grouped video result UI with lead scene, preview strip, expand/collapse control, and scene click handling.
- `frontend/src/components/SearchResultGroup.test.tsx` — component tests for previews, expansion, and opening the selected scene.

### Modified files
- `frontend/src/pages/SearchPage.tsx` — replace direct flat-result rendering with grouped render entries while keeping search, filtering, sorting, empty states, and summary copy.
- `frontend/src/pages/SearchPage.test.tsx` — add integration coverage for grouped video results on the page.

### Existing files left unchanged unless needed by test breakage
- `frontend/src/components/SearchResultCard.tsx` — keep standalone image and scene-card behavior unchanged.
- `frontend/src/components/SearchResultCard.test.tsx` — only update if existing assertions break while preserving current behavior.

---

### Task 1: Add grouped-result utility

**Files:**
- Create: `frontend/src/utils/searchResults.ts`
- Create: `frontend/src/utils/searchResults.test.ts`

- [ ] **Step 1: Write the failing grouping tests**

Create `frontend/src/utils/searchResults.test.ts` with these tests:

```ts
import { describe, expect, it } from 'vitest'

import { buildSearchRenderEntries } from './searchResults'
import type { SearchResult } from '../types/api'

function makeScene(overrides: Partial<SearchResult>): SearchResult {
  return {
    media_id: 100,
    scene_id: 1,
    media_type: 'video',
    result_type: 'video_scene',
    original_filename: 'demo.mp4',
    score: 0.8,
    vector_score: 0.7,
    keyword_score: 0.4,
    caption: 'scene caption',
    file_url: '/media/demo.mp4',
    thumbnail_url: '/media/demo-1.jpg',
    start_time: 10,
    end_time: 15,
    explanation: {
      match_type: 'hybrid',
      exact_phrase_match: false,
      rich_caption: false,
      rerank_boost: 0,
    },
    ...overrides,
  }
}

function makeImage(overrides: Partial<SearchResult>): SearchResult {
  return {
    media_id: 200,
    scene_id: null,
    media_type: 'image',
    result_type: 'image',
    original_filename: 'photo.jpg',
    score: 0.6,
    vector_score: 0.6,
    keyword_score: 0,
    caption: 'image caption',
    file_url: '/media/photo.jpg',
    thumbnail_url: '/media/photo.jpg',
    start_time: null,
    end_time: null,
    explanation: {
      match_type: 'visual',
      exact_phrase_match: false,
      rich_caption: false,
      rerank_boost: 0,
    },
    ...overrides,
  }
}

describe('buildSearchRenderEntries', () => {
  it('groups scenes from the same video under the best-scoring scene position', () => {
    const firstVideo = makeScene({ media_id: 10, scene_id: 11, score: 0.92, start_time: 12, end_time: 18 })
    const image = makeImage({ media_id: 20, score: 0.88, original_filename: 'office.jpg' })
    const secondScene = makeScene({ media_id: 10, scene_id: 12, score: 0.79, start_time: 28, end_time: 34 })
    const thirdScene = makeScene({ media_id: 10, scene_id: 13, score: 0.73, start_time: 40, end_time: 48 })

    const entries = buildSearchRenderEntries([firstVideo, image, secondScene, thirdScene])

    expect(entries).toHaveLength(2)
    expect(entries[0]).toMatchObject({
      kind: 'video-group',
      mediaId: 10,
      lead: { scene_id: 11, score: 0.92 },
    })
    expect(entries[1]).toMatchObject({
      kind: 'single',
      item: { media_id: 20, original_filename: 'office.jpg' },
    })

    if (entries[0].kind !== 'video-group') {
      throw new Error('expected video-group entry')
    }

    expect(entries[0].previews.map((item) => item.scene_id)).toEqual([12, 13])
    expect(entries[0].hidden).toEqual([])
  })

  it('keeps images and single-scene videos as standalone entries', () => {
    const image = makeImage({ media_id: 30 })
    const singleScene = makeScene({ media_id: 40, scene_id: 41, score: 0.81 })

    const entries = buildSearchRenderEntries([image, singleScene])

    expect(entries).toHaveLength(2)
    expect(entries[0]).toMatchObject({ kind: 'single', item: { media_id: 30 } })
    expect(entries[1]).toMatchObject({ kind: 'single', item: { media_id: 40, scene_id: 41 } })
  })

  it('limits collapsed previews to two scenes and leaves the rest hidden', () => {
    const entries = buildSearchRenderEntries([
      makeScene({ media_id: 50, scene_id: 51, score: 0.95, start_time: 5, end_time: 9 }),
      makeScene({ media_id: 50, scene_id: 52, score: 0.84, start_time: 15, end_time: 19 }),
      makeScene({ media_id: 50, scene_id: 53, score: 0.78, start_time: 25, end_time: 29 }),
      makeScene({ media_id: 50, scene_id: 54, score: 0.71, start_time: 35, end_time: 39 }),
    ])

    expect(entries).toHaveLength(1)

    if (entries[0].kind !== 'video-group') {
      throw new Error('expected video-group entry')
    }

    expect(entries[0].lead.scene_id).toBe(51)
    expect(entries[0].previews.map((item) => item.scene_id)).toEqual([52, 53])
    expect(entries[0].hidden.map((item) => item.scene_id)).toEqual([54])
  })
})
```

- [ ] **Step 2: Run the utility tests to verify they fail**

Run:

```bash
npm test -- src/utils/searchResults.test.ts
```

Expected: FAIL with a module-not-found error for `./searchResults`.

- [ ] **Step 3: Write the minimal grouping utility**

Create `frontend/src/utils/searchResults.ts` with this implementation:

```ts
import type { SearchResult } from '../types/api'

export type SearchRenderEntry =
  | {
      kind: 'single'
      item: SearchResult
    }
  | {
      kind: 'video-group'
      mediaId: number
      lead: SearchResult
      previews: SearchResult[]
      hidden: SearchResult[]
    }

export function buildSearchRenderEntries(results: SearchResult[]): SearchRenderEntry[] {
  const entries: SearchRenderEntry[] = []
  const videoGroups = new Map<number, SearchResult[]>()
  const insertedVideoGroups = new Set<number>()

  for (const result of results) {
    if (result.result_type !== 'video_scene') {
      entries.push({ kind: 'single', item: result })
      continue
    }

    const group = videoGroups.get(result.media_id)
    if (group) {
      group.push(result)
    } else {
      videoGroups.set(result.media_id, [result])
    }
  }

  for (const result of results) {
    if (result.result_type !== 'video_scene') {
      continue
    }

    if (insertedVideoGroups.has(result.media_id)) {
      continue
    }

    const scenes = videoGroups.get(result.media_id) ?? [result]

    if (scenes.length === 1) {
      entries.push({ kind: 'single', item: scenes[0] })
    } else {
      entries.push({
        kind: 'video-group',
        mediaId: result.media_id,
        lead: scenes[0],
        previews: scenes.slice(1, 3),
        hidden: scenes.slice(3),
      })
    }

    insertedVideoGroups.add(result.media_id)
  }

  return entries.filter((entry, index, allEntries) => {
    if (entry.kind === 'single' && entry.item.result_type === 'image') {
      return true
    }

    if (entry.kind === 'single' && entry.item.result_type === 'video_scene') {
      return true
    }

    if (entry.kind === 'video-group') {
      return allEntries.findIndex((candidate) => candidate.kind === 'video-group' && candidate.mediaId === entry.mediaId) === index
    }

    return true
  })
}
```

- [ ] **Step 4: Fix the ordering bug so grouped videos stay in the lead-scene position**

Replace `buildSearchRenderEntries()` with this corrected version that emits entries in one pass over the sorted results:

```ts
export function buildSearchRenderEntries(results: SearchResult[]): SearchRenderEntry[] {
  const entries: SearchRenderEntry[] = []
  const groupedScenes = new Map<number, SearchResult[]>()

  for (const result of results) {
    if (result.result_type === 'video_scene') {
      const existing = groupedScenes.get(result.media_id)
      if (existing) {
        existing.push(result)
      } else {
        groupedScenes.set(result.media_id, [result])
      }
    }
  }

  const emittedVideoGroups = new Set<number>()

  for (const result of results) {
    if (result.result_type !== 'video_scene') {
      entries.push({ kind: 'single', item: result })
      continue
    }

    if (emittedVideoGroups.has(result.media_id)) {
      continue
    }

    const scenes = groupedScenes.get(result.media_id) ?? [result]
    emittedVideoGroups.add(result.media_id)

    if (scenes.length === 1) {
      entries.push({ kind: 'single', item: scenes[0] })
      continue
    }

    entries.push({
      kind: 'video-group',
      mediaId: result.media_id,
      lead: scenes[0],
      previews: scenes.slice(1, 3),
      hidden: scenes.slice(3),
    })
  }

  return entries
}
```

- [ ] **Step 5: Run the utility tests to verify they pass**

Run:

```bash
npm test -- src/utils/searchResults.test.ts
```

Expected: PASS with 3 passing tests.

- [ ] **Step 6: Commit**

```bash
git add src/utils/searchResults.ts src/utils/searchResults.test.ts
git commit -m "feat: group video search results"
```

---

### Task 2: Add grouped video result component

**Files:**
- Create: `frontend/src/components/SearchResultGroup.tsx`
- Create: `frontend/src/components/SearchResultGroup.test.tsx`
- Read for reuse: `frontend/src/components/SearchResultCard.tsx`
- Read for reuse: `frontend/src/utils/format.ts`

- [ ] **Step 1: Write the failing grouped-result component tests**

Create `frontend/src/components/SearchResultGroup.test.tsx` with these tests:

```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { SearchResultGroup } from './SearchResultGroup'
import type { SearchResult } from '../types/api'

const onOpenMedia = vi.fn()

function makeScene(sceneId: number, startTime: number, score: number): SearchResult {
  return {
    media_id: 9,
    scene_id: sceneId,
    media_type: 'video',
    result_type: 'video_scene',
    original_filename: 'workshop.mp4',
    score,
    vector_score: score - 0.1,
    keyword_score: 0.4,
    caption: `scene ${sceneId}`,
    file_url: '/media/workshop.mp4',
    thumbnail_url: `/media/workshop-${sceneId}.jpg`,
    start_time: startTime,
    end_time: startTime + 6,
    explanation: {
      match_type: 'hybrid',
      exact_phrase_match: sceneId === 1,
      rich_caption: sceneId === 1,
      rerank_boost: 0.1,
    },
  }
}

describe('SearchResultGroup', () => {
  it('shows the lead scene, preview strip, and expansion control', () => {
    render(
      <SearchResultGroup
        mediaId={9}
        lead={makeScene(1, 12, 0.91)}
        previews={[makeScene(2, 26, 0.84), makeScene(3, 40, 0.8)]}
        hidden={[makeScene(4, 54, 0.72)]}
        onOpenMedia={onOpenMedia}
      />,
    )

    expect(screen.getByRole('button', { name: 'Open workshop.mp4' })).toBeInTheDocument()
    expect(screen.getByText('0:26 - 0:32')).toBeInTheDocument()
    expect(screen.getByText('0:40 - 0:46')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Show 1 more scenes' })).toBeInTheDocument()
  })

  it('expands hidden scenes inline and opens the selected preview scene', () => {
    render(
      <SearchResultGroup
        mediaId={9}
        lead={makeScene(1, 12, 0.91)}
        previews={[makeScene(2, 26, 0.84)]}
        hidden={[makeScene(3, 40, 0.8)]}
        onOpenMedia={onOpenMedia}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Open scene 2 at 0:26 - 0:32' }))
    expect(onOpenMedia).toHaveBeenCalledWith(9, 26)

    fireEvent.click(screen.getByRole('button', { name: 'Show 1 more scenes' }))
    expect(screen.getByRole('button', { name: 'Hide extra scenes' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Open scene 3 at 0:40 - 0:46' })).toBeInTheDocument()
  })

  it('omits the preview strip and expansion control for single-scene groups', () => {
    render(
      <SearchResultGroup
        mediaId={9}
        lead={makeScene(1, 12, 0.91)}
        previews={[]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />,
    )

    expect(screen.queryByText(/Show \d+ more scenes/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Open scene 2/ })).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the grouped-result component tests to verify they fail**

Run:

```bash
npm test -- src/components/SearchResultGroup.test.tsx
```

Expected: FAIL with a module-not-found error for `./SearchResultGroup`.

- [ ] **Step 3: Write the grouped video result component**

Create `frontend/src/components/SearchResultGroup.tsx` with this implementation:

```tsx
import { useState } from 'react'

import { Badge, Button } from '@/components/ui'
import { cn } from '@/lib/utils'

import type { SearchResult } from '../types/api'
import { formatScore, formatTimeRange, toAbsoluteUrl } from '../utils/format'
import { SearchResultCard } from './SearchResultCard'

interface SearchResultGroupProps {
  mediaId: number
  lead: SearchResult
  previews: SearchResult[]
  hidden: SearchResult[]
  onOpenMedia: (mediaId: number, startTime: number | null) => void
  className?: string
  isFocused?: boolean
}

function ScenePreviewButton({
  item,
  onOpenMedia,
  className,
}: {
  item: SearchResult
  onOpenMedia: (mediaId: number, startTime: number | null) => void
  className?: string
}) {
  const thumbnailUrl = toAbsoluteUrl(item.thumbnail_url || item.file_url)
  const label = formatTimeRange(item.start_time, item.end_time)

  return (
    <button
      type="button"
      className={cn(
        'flex min-w-0 items-center gap-3 rounded-lg border border-border bg-background p-2 text-left transition-colors hover:bg-muted/40 focus:outline-none focus:ring-2 focus:ring-ring',
        className,
      )}
      onClick={() => onOpenMedia(item.media_id, item.start_time)}
      aria-label={`Open scene ${item.scene_id} at ${label}`}
    >
      <div className="h-14 w-20 shrink-0 overflow-hidden rounded-md bg-muted">
        {thumbnailUrl ? (
          <img src={thumbnailUrl} alt="" className="h-full w-full object-cover" loading="lazy" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xs text-muted-foreground">Video</div>
        )}
      </div>
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="text-[11px]">
            {label}
          </Badge>
          <Badge variant="outline" className="text-[11px]">
            {formatScore(item.score)}
          </Badge>
        </div>
        <p className="line-clamp-2 text-xs text-muted-foreground">{item.caption}</p>
      </div>
    </button>
  )
}

export function SearchResultGroup({
  mediaId,
  lead,
  previews,
  hidden,
  onOpenMedia,
  className,
  isFocused = false,
}: SearchResultGroupProps) {
  const [expanded, setExpanded] = useState(false)
  const hiddenCount = hidden.length

  return (
    <div className={cn('space-y-3', className)} data-media-id={mediaId}>
      <SearchResultCard item={lead} onOpenMedia={onOpenMedia} isFocused={isFocused} />

      {previews.length > 0 && (
        <div className="space-y-2 rounded-lg border border-border bg-muted/20 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">More matching scenes</p>
          <div className="grid grid-cols-1 gap-2">
            {previews.map((item) => (
              <ScenePreviewButton key={item.scene_id ?? item.start_time ?? item.score} item={item} onOpenMedia={onOpenMedia} />
            ))}
          </div>
        </div>
      )}

      {hiddenCount > 0 && (
        <div className="space-y-3">
          <Button type="button" variant="outline" onClick={() => setExpanded((current) => !current)}>
            {expanded ? 'Hide extra scenes' : `Show ${hiddenCount} more scenes`}
          </Button>

          {expanded && (
            <div className="grid grid-cols-1 gap-2 rounded-lg border border-border bg-muted/10 p-3">
              {hidden.map((item) => (
                <ScenePreviewButton
                  key={item.scene_id ?? item.start_time ?? item.score}
                  item={item}
                  onOpenMedia={onOpenMedia}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run the grouped-result component tests to verify they pass**

Run:

```bash
npm test -- src/components/SearchResultGroup.test.tsx
```

Expected: PASS with 3 passing tests.

- [ ] **Step 5: Commit**

```bash
git add src/components/SearchResultGroup.tsx src/components/SearchResultGroup.test.tsx
git commit -m "feat: add grouped video result card"
```

---

### Task 3: Integrate grouped entries into the search page

**Files:**
- Modify: `frontend/src/pages/SearchPage.tsx`
- Modify: `frontend/src/pages/SearchPage.test.tsx`
- Read for reuse: `frontend/src/api/client.ts`
- Read for reuse: `frontend/src/utils/searchResults.ts`
- Read for reuse: `frontend/src/components/SearchResultGroup.tsx`

- [ ] **Step 1: Write the failing SearchPage integration tests**

Replace `frontend/src/pages/SearchPage.test.tsx` with this test file:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { SearchPage } from './SearchPage'
import { searchMedia } from '../api/client'

vi.mock('../api/client', () => ({
  searchMedia: vi.fn(),
  searchMediaByImage: vi.fn(),
}))

const mockedSearchMedia = vi.mocked(searchMedia)

beforeEach(() => {
  mockedSearchMedia.mockReset()
  window.localStorage.clear()
})

describe('SearchPage score filter', () => {
  it('shows results with scores below 0.5 when default filter is permissive', () => {
    const mockOnOpenMedia = () => {}

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const [, scoreSelect] = screen.getAllByRole('combobox')
    expect(scoreSelect).toHaveTextContent('≥ 0.0')
  })

  it('starts without ranking explanation copy before any search results exist', () => {
    const mockOnOpenMedia = () => {}

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    expect(screen.queryByText(/Semantic/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Rich caption/)).not.toBeInTheDocument()
  })
})

describe('SearchPage grouped video scenes', () => {
  it('groups related video scenes and keeps images as standalone results', async () => {
    mockedSearchMedia.mockResolvedValue({
      query_mode: 'text',
      query_text: 'office',
      count: 4,
      results: [
        {
          media_id: 10,
          scene_id: 11,
          media_type: 'video',
          result_type: 'video_scene',
          original_filename: 'demo.mp4',
          score: 0.93,
          vector_score: 0.88,
          keyword_score: 0.4,
          caption: 'lead scene',
          file_url: '/media/demo.mp4',
          thumbnail_url: '/media/demo-11.jpg',
          start_time: 12,
          end_time: 18,
          explanation: {
            match_type: 'hybrid',
            exact_phrase_match: true,
            rich_caption: true,
            rerank_boost: 0.1,
          },
        },
        {
          media_id: 20,
          scene_id: null,
          media_type: 'image',
          result_type: 'image',
          original_filename: 'office.jpg',
          score: 0.87,
          vector_score: 0.87,
          keyword_score: 0,
          caption: 'office image',
          file_url: '/media/office.jpg',
          thumbnail_url: '/media/office.jpg',
          start_time: null,
          end_time: null,
          explanation: {
            match_type: 'visual',
            exact_phrase_match: false,
            rich_caption: false,
            rerank_boost: 0,
          },
        },
        {
          media_id: 10,
          scene_id: 12,
          media_type: 'video',
          result_type: 'video_scene',
          original_filename: 'demo.mp4',
          score: 0.82,
          vector_score: 0.77,
          keyword_score: 0.38,
          caption: 'preview scene',
          file_url: '/media/demo.mp4',
          thumbnail_url: '/media/demo-12.jpg',
          start_time: 25,
          end_time: 31,
          explanation: {
            match_type: 'hybrid',
            exact_phrase_match: false,
            rich_caption: false,
            rerank_boost: 0,
          },
        },
        {
          media_id: 10,
          scene_id: 13,
          media_type: 'video',
          result_type: 'video_scene',
          original_filename: 'demo.mp4',
          score: 0.76,
          vector_score: 0.7,
          keyword_score: 0.33,
          caption: 'second preview scene',
          file_url: '/media/demo.mp4',
          thumbnail_url: '/media/demo-13.jpg',
          start_time: 40,
          end_time: 46,
          explanation: {
            match_type: 'hybrid',
            exact_phrase_match: false,
            rich_caption: false,
            rerank_boost: 0,
          },
        },
      ],
    })

    render(<SearchPage onOpenMedia={() => {}} />)

    fireEvent.change(screen.getByLabelText('Search query'), { target: { value: 'office' } })

    await waitFor(() => {
      expect(screen.getByText('2 results for "office"')).toBeInTheDocument()
    })

    expect(screen.getAllByRole('button', { name: 'Open demo.mp4' })).toHaveLength(1)
    expect(screen.getByText('office.jpg')).toBeInTheDocument()
    expect(screen.getByText('0:25 - 0:31')).toBeInTheDocument()
    expect(screen.getByText('0:40 - 0:46')).toBeInTheDocument()
  })

  it('expands hidden scenes and opens the selected scene timestamp', async () => {
    const onOpenMedia = vi.fn()

    mockedSearchMedia.mockResolvedValue({
      query_mode: 'text',
      query_text: 'workshop',
      count: 4,
      results: [
        {
          media_id: 99,
          scene_id: 1,
          media_type: 'video',
          result_type: 'video_scene',
          original_filename: 'workshop.mp4',
          score: 0.94,
          vector_score: 0.89,
          keyword_score: 0.41,
          caption: 'lead scene',
          file_url: '/media/workshop.mp4',
          thumbnail_url: '/media/workshop-1.jpg',
          start_time: 10,
          end_time: 16,
          explanation: {
            match_type: 'hybrid',
            exact_phrase_match: true,
            rich_caption: true,
            rerank_boost: 0.1,
          },
        },
        {
          media_id: 99,
          scene_id: 2,
          media_type: 'video',
          result_type: 'video_scene',
          original_filename: 'workshop.mp4',
          score: 0.82,
          vector_score: 0.75,
          keyword_score: 0.35,
          caption: 'preview scene',
          file_url: '/media/workshop.mp4',
          thumbnail_url: '/media/workshop-2.jpg',
          start_time: 24,
          end_time: 30,
          explanation: {
            match_type: 'hybrid',
            exact_phrase_match: false,
            rich_caption: false,
            rerank_boost: 0,
          },
        },
        {
          media_id: 99,
          scene_id: 3,
          media_type: 'video',
          result_type: 'video_scene',
          original_filename: 'workshop.mp4',
          score: 0.79,
          vector_score: 0.72,
          keyword_score: 0.32,
          caption: 'second preview scene',
          file_url: '/media/workshop.mp4',
          thumbnail_url: '/media/workshop-3.jpg',
          start_time: 38,
          end_time: 44,
          explanation: {
            match_type: 'hybrid',
            exact_phrase_match: false,
            rich_caption: false,
            rerank_boost: 0,
          },
        },
        {
          media_id: 99,
          scene_id: 4,
          media_type: 'video',
          result_type: 'video_scene',
          original_filename: 'workshop.mp4',
          score: 0.71,
          vector_score: 0.67,
          keyword_score: 0.28,
          caption: 'hidden scene',
          file_url: '/media/workshop.mp4',
          thumbnail_url: '/media/workshop-4.jpg',
          start_time: 52,
          end_time: 58,
          explanation: {
            match_type: 'hybrid',
            exact_phrase_match: false,
            rich_caption: false,
            rerank_boost: 0,
          },
        },
      ],
    })

    render(<SearchPage onOpenMedia={onOpenMedia} />)

    fireEvent.change(screen.getByLabelText('Search query'), { target: { value: 'workshop' } })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Show 1 more scenes' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Show 1 more scenes' }))
    fireEvent.click(screen.getByRole('button', { name: 'Open scene 4 at 0:52 - 0:58' }))

    expect(onOpenMedia).toHaveBeenCalledWith(99, 52)
  })
})
```

- [ ] **Step 2: Run the SearchPage integration tests to verify they fail for the expected reason**

Run:

```bash
npm test -- src/pages/SearchPage.test.tsx
```

Expected: FAIL because the page still renders a flat result list and the grouped-scene assertions do not match.

- [ ] **Step 3: Import the grouping utility and grouped-result component into `SearchPage.tsx`**

Add these imports near the top of `frontend/src/pages/SearchPage.tsx`:

```ts
import { SearchResultGroup } from '../components/SearchResultGroup'
import { buildSearchRenderEntries } from '../utils/searchResults'
```

- [ ] **Step 4: Replace the flat result derivation with grouped render entries**

In `frontend/src/pages/SearchPage.tsx`, replace the current `filteredAndSortedResults` constant with this pair:

```ts
  const filteredAndSortedResults = deferredResults
    .filter((result) => {
      if (typeFilter === 'all') return true
      if (typeFilter === 'images') return result.media_type === 'image'
      if (typeFilter === 'videos') return result.media_type === 'video'
      return true
    })
    .filter((result) => {
      const threshold = parseFloat(scoreFilter)
      return result.score >= threshold
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'relevance':
          return b.score - a.score
        case 'date':
          return b.original_filename.localeCompare(a.original_filename)
        case 'size':
          return a.original_filename.localeCompare(b.original_filename)
        default:
          return b.score - a.score
      }
    })

  const renderEntries = buildSearchRenderEntries(filteredAndSortedResults)
```

- [ ] **Step 5: Update keyboard navigation to use the grouped render entries**

In the window `keydown` effect, replace `filteredAndSortedResults.length` and the Enter handler lookup with this logic:

```ts
      if (renderEntries.length === 0) return
```

```ts
        setFocusedResultIndex((prev) =>
          prev < renderEntries.length - 1 ? prev + 1 : prev,
        )
```

```ts
        const entry = renderEntries[focusedResultIndex]
        if (!entry) {
          return
        }

        if (entry.kind === 'single') {
          onOpenMedia(entry.item.media_id, entry.item.start_time)
          return
        }

        onOpenMedia(entry.lead.media_id, entry.lead.start_time)
```

And update the effect dependency list to use `renderEntries` instead of `filteredAndSortedResults`.

- [ ] **Step 6: Update the empty-state and summary counts to use grouped entries**

Replace these checks and summary strings:

```tsx
      {searchedLabel && !loading && filteredAndSortedResults.length === 0 && !error && (
```

with:

```tsx
      {searchedLabel && !loading && renderEntries.length === 0 && !error && (
```

Replace the summary heading:

```tsx
              {filteredAndSortedResults.length} result{filteredAndSortedResults.length === 1 ? '' : 's'} for {emptyStateLabel}
```

with:

```tsx
              {renderEntries.length} result{renderEntries.length === 1 ? '' : 's'} for {emptyStateLabel}
```

- [ ] **Step 7: Replace the flat results grid rendering with grouped entry rendering**

Replace the grid mapping block with this implementation:

```tsx
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {renderEntries.map((entry, index) => {
              const key =
                entry.kind === 'single'
                  ? `${entry.item.result_type}-${entry.item.media_id}-${entry.item.start_time ?? 'image'}`
                  : `video-group-${entry.mediaId}`

              return (
                <div
                  key={key}
                  className="animate-in fade-in-0 duration-150"
                  style={{ animationDelay: `${index * 30}ms` }}
                >
                  {entry.kind === 'single' ? (
                    <SearchResultCard
                      item={entry.item}
                      onOpenMedia={onOpenMedia}
                      isFocused={index === focusedResultIndex}
                    />
                  ) : (
                    <SearchResultGroup
                      mediaId={entry.mediaId}
                      lead={entry.lead}
                      previews={entry.previews}
                      hidden={entry.hidden}
                      onOpenMedia={onOpenMedia}
                      isFocused={index === focusedResultIndex}
                    />
                  )}
                </div>
              )
            })}
          </div>
```

- [ ] **Step 8: Run the SearchPage integration tests to verify they pass**

Run:

```bash
npm test -- src/pages/SearchPage.test.tsx
```

Expected: PASS with 4 passing tests.

- [ ] **Step 9: Run the focused frontend test set to catch regressions**

Run:

```bash
npm test -- src/utils/searchResults.test.ts src/components/SearchResultGroup.test.tsx src/components/SearchResultCard.test.tsx src/pages/SearchPage.test.tsx
```

Expected: PASS with all related tests green.

- [ ] **Step 10: Commit**

```bash
git add src/pages/SearchPage.tsx src/pages/SearchPage.test.tsx src/components/SearchResultGroup.tsx src/components/SearchResultGroup.test.tsx src/utils/searchResults.ts src/utils/searchResults.test.ts
git commit -m "feat: group related video scenes in search results"
```

---

### Task 4: Verify the frontend build and behavior

**Files:**
- Modify only if verification exposes a defect in existing task files.

- [ ] **Step 1: Run the full frontend test suite**

Run:

```bash
npm test
```

Expected: PASS.

- [ ] **Step 2: Run the frontend build**

Run:

```bash
npm run build
```

Expected: PASS with a production build emitted by Vite.

- [ ] **Step 3: Start the frontend dev server**

Run:

```bash
npm run dev
```

Expected: Vite dev server starts and prints a local URL.

- [ ] **Step 4: Manually verify grouped video-scene behavior in the browser**

Check these behaviors against a search query that returns multiple scenes from the same video:

1. The best scene for a video is visible in the grid immediately.
2. The next one or two scenes appear in the preview strip.
3. `Show N more scenes` appears only when additional hidden scenes exist.
4. Expanding reveals the remaining scenes inline.
5. Clicking a preview or expanded scene opens the correct timestamp.
6. Standalone image results still render exactly once and keep their existing badges.

- [ ] **Step 5: If UI behavior differs, add the smallest failing test before fixing it**

Use one of these commands depending on where the defect appears:

```bash
npm test -- src/components/SearchResultGroup.test.tsx
```

```bash
npm test -- src/pages/SearchPage.test.tsx
```

Expected: FAIL first for the newly identified behavior, then fix with the smallest code change.

- [ ] **Step 6: Commit the verified final state**

```bash
git add src/pages/SearchPage.tsx src/pages/SearchPage.test.tsx src/components/SearchResultGroup.tsx src/components/SearchResultGroup.test.tsx src/utils/searchResults.ts src/utils/searchResults.test.ts
git commit -m "test: verify grouped video scene presentation"
```

---

## Spec Coverage Check

- Group related `video_scene` results by `media_id` — covered in Task 1 and Task 3.
- Keep image results unchanged — covered in Task 1 tests and Task 3 integration tests.
- Show the best scene first — covered in Task 1 and Task 2.
- Show a preview strip for the next one or two scenes — covered in Task 1, Task 2, and Task 3.
- Add inline expansion for remaining scenes — covered in Task 2 and Task 3.
- Open the correct timestamp for any visible scene — covered in Task 2 and Task 3.
- Preserve keyboard reachability and top-level focus behavior — covered in Task 2 and Task 3.
- Verify real frontend behavior after coding — covered in Task 4.

## Placeholder Scan

- No `TODO`, `TBD`, or deferred implementation markers remain in the task steps.
- Every code-writing step includes concrete code.
- Every verification step includes an exact command and expected outcome.

## Type Consistency Check

- `buildSearchRenderEntries()` produces `SearchRenderEntry` values consumed by `SearchPage.tsx`.
- `SearchResultGroup` accepts `mediaId`, `lead`, `previews`, `hidden`, and `onOpenMedia`.
- Preview and expanded scene buttons always call `onOpenMedia(item.media_id, item.start_time)`.

Plan complete and saved to `Semedia/docs/superpowers/plans/2026-05-02-phase6-task-6-3-video-scene-grouping.md`.

Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
