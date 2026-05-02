# Phase 6.2 Rich Ranking Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose vector and keyword component scores plus a compact explanation object in search results, then render that explanation in the frontend result cards.

**Architecture:** Keep all ranking math in the existing shared ranking pipeline. Add one small explanation helper in `services/shared/semedia_shared/ranking_service.py`, one serializer helper in `services/shared/semedia_shared/search_service.py`, and extend the existing frontend `SearchResultCard` to translate those fields into short user-facing labels.

**Tech Stack:** Python, FastAPI, SQLAlchemy, React 19, TypeScript, Vitest, Testing Library, Docker Compose

---

## File Map

### Files to modify
- `services/shared/semedia_shared/ranking_service.py` — add a helper that derives `match_type`, phrase/rich-caption flags, and `rerank_boost` from already-ranked candidates.
- `services/shared/semedia_shared/search_service.py` — serialize ranked candidates into the richer API payload for both text and image search.
- `testing/services/test_ranking_service.py` — add focused unit coverage for explanation semantics.
- `testing/services/test_search_api.py` — add API-level coverage that the richer response fields are returned to clients.
- `frontend/src/types/api.ts` — extend `SearchResult` with `scene_id`, component scores, and the `explanation` object.
- `frontend/src/components/SearchResultCard.tsx` — render a compact explanation summary and component breakdown row.

### Files to create
- `frontend/src/components/SearchResultCard.test.tsx` — frontend rendering tests for the new explanation UI.

### Reference-only files
- `services/search_api/app/main.py` — no code change expected; the route already returns the `search_service.py` payload unchanged.
- `services/gateway_api/app/main.py` — no code change expected; the gateway already proxies search JSON unchanged.
- `frontend/src/pages/SearchPage.tsx` — no code change expected; it already passes each result object through to `SearchResultCard`.

### Execution note
- Do not create git commits while executing this plan. The user handles commits in this workspace.

---

### Task 1: Add an explanation helper to the ranking layer

**Files:**
- Modify: `services/shared/semedia_shared/ranking_service.py`
- Test: `testing/services/test_ranking_service.py`

- [ ] **Step 1: Add failing unit tests for explanation semantics**

Append these tests to `testing/services/test_ranking_service.py`:

```python
from semedia_shared.ranking_service import (
    _apply_diversity,
    _apply_reranking,
    _calibrate_scores,
    build_result_explanation,
    merge_candidates,
    rank_candidates,
)


def test_build_result_explanation_marks_caption_match(test_settings):
    candidate = {
        "caption": "office desk",
        "vector_score": 0.3,
        "keyword_score": 1.0,
        "fusion_score": 0.51,
        "rerank_score": 0.59,
    }

    explanation = build_result_explanation(candidate, query_text="office desk", query_mode="text")

    assert explanation == {
        "match_type": "caption",
        "exact_phrase_match": True,
        "rich_caption": False,
        "rerank_boost": 0.08,
    }


def test_build_result_explanation_marks_hybrid_match_with_rich_caption(test_settings):
    candidate = {
        "caption": "office desk workspace laptop with bright window light and conference notebooks",
        "vector_score": 0.8,
        "keyword_score": 0.4,
        "fusion_score": 0.68,
        "rerank_score": 0.78,
    }

    explanation = build_result_explanation(candidate, query_text="office desk", query_mode="text")

    assert explanation == {
        "match_type": "hybrid",
        "exact_phrase_match": True,
        "rich_caption": True,
        "rerank_boost": 0.1,
    }


def test_build_result_explanation_marks_image_results_as_visual(test_settings):
    candidate = {
        "caption": "a red square",
        "vector_score": 0.9,
        "keyword_score": 0.0,
        "fusion_score": 0.9,
        "rerank_score": 0.9,
    }

    explanation = build_result_explanation(candidate, query_text=None, query_mode="image")

    assert explanation == {
        "match_type": "visual",
        "exact_phrase_match": False,
        "rich_caption": False,
        "rerank_boost": 0.0,
    }
```

- [ ] **Step 2: Run the new ranking tests and confirm they fail**

Run from `Semedia/`:

```powershell
docker compose --profile test run --rm --build service-tests pytest testing/services/test_ranking_service.py -v
```

Expected: FAIL with an import or attribute error because `build_result_explanation` does not exist yet.

- [ ] **Step 3: Implement the explanation helper in the ranking layer**

Add this helper near `_calibrate_scores()` in `services/shared/semedia_shared/ranking_service.py`:

```python
def build_result_explanation(candidate: dict, *, query_text: str | None, query_mode: str) -> dict:
    vector_score = _clamp_score(candidate.get("vector_score", 0.0))
    keyword_score = _clamp_score(candidate.get("keyword_score", 0.0))
    fusion_score = _clamp_score(candidate.get("fusion_score", vector_score if query_mode == "image" else 0.0))
    rerank_score = _clamp_score(candidate.get("rerank_score", fusion_score))

    normalized_query = _normalize_text(query_text or "")
    normalized_caption = _normalize_text(candidate.get("caption", ""))
    exact_phrase_match = bool(
        query_mode == "text" and normalized_query and normalized_query in normalized_caption
    )
    rich_caption = bool(
        query_mode == "text" and len(candidate.get("caption", "").strip()) > _RICH_CAPTION_LENGTH
    )

    if query_mode == "image" or keyword_score == 0.0:
        match_type = "visual"
    elif vector_score == 0.0 or keyword_score > vector_score:
        match_type = "caption"
    else:
        match_type = "hybrid"

    return {
        "match_type": match_type,
        "exact_phrase_match": exact_phrase_match,
        "rich_caption": rich_caption,
        "rerank_boost": round(max(0.0, rerank_score - fusion_score), 4),
    }
```

Also update the import list in `testing/services/test_ranking_service.py` to include `build_result_explanation`.

- [ ] **Step 4: Re-run the ranking tests and confirm they pass**

Run from `Semedia/`:

```powershell
docker compose --profile test run --rm --build service-tests pytest testing/services/test_ranking_service.py -v
```

Expected: PASS for the three new explanation tests and the existing ranking tests.

---

### Task 2: Expose component scores and explanation fields in the search API payload

**Files:**
- Modify: `services/shared/semedia_shared/search_service.py`
- Test: `testing/services/test_search_api.py`

- [ ] **Step 1: Add failing API tests for text and image search payloads**

Append these tests to `testing/services/test_search_api.py`:

```python
def test_search_text_returns_component_scores_and_explanation(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/office.jpg",
            original_filename="office.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="office desk",
            embedding=[0.3, 0.0],
            index_key="media:90",
        )
        session.add(image)
        session.commit()
        session.refresh(image)

    monkeypatch.setattr(module, "_embed_text", lambda query_text: [1.0, 0.0])

    response = client.post("/api/v1/search/", json={"query_text": "office desk", "top_k": 5})

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["media_id"] == image.id
    assert result["vector_score"] == 0.3
    assert result["keyword_score"] == 1.0
    assert result["explanation"] == {
        "match_type": "caption",
        "exact_phrase_match": True,
        "rich_caption": False,
        "rerank_boost": 0.08,
    }


def test_image_search_returns_visual_explanation(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        image = MediaItem(
            file_path="originals/red.jpg",
            original_filename="red.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="a red square",
            embedding=[1.0, 0.0],
            index_key="media:91",
        )
        session.add(image)
        session.commit()
        session.refresh(image)

    monkeypatch.setattr(module, "_embed_image", lambda file: [1.0, 0.0])

    response = client.post(
        "/api/v1/search/by-image/",
        data={"top_k": "5"},
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["media_id"] == image.id
    assert result["vector_score"] == 1.0
    assert result["keyword_score"] == 0.0
    assert result["explanation"] == {
        "match_type": "visual",
        "exact_phrase_match": False,
        "rich_caption": False,
        "rerank_boost": 0.0,
    }
```

- [ ] **Step 2: Run the new API tests and confirm they fail**

Run from `Semedia/`:

```powershell
docker compose --profile test run --rm --build service-tests pytest testing/services/test_search_api.py -v
```

Expected: FAIL with missing `vector_score`, `keyword_score`, or `explanation` fields in the response JSON.

- [ ] **Step 3: Add a serializer helper to `search_service.py`**

Update the imports at the top of `services/shared/semedia_shared/search_service.py`:

```python
from .ranking_service import build_result_explanation, merge_candidates, rank_candidates
```

Then add a serializer helper above `search_text()`:

```python
def _serialize_score(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _serialize_ranked_result(item: dict, *, query_text: str | None, query_mode: str) -> dict:
    return {
        "media_id": item["media_id"],
        "scene_id": item.get("scene_id"),
        "media_type": item["media_type"],
        "result_type": item["result_type"],
        "original_filename": item["original_filename"],
        "score": _serialize_score(item["score"]),
        "vector_score": _serialize_score(item.get("vector_score", 0.0)),
        "keyword_score": _serialize_score(item.get("keyword_score", 0.0)),
        "caption": item.get("caption", ""),
        "file_url": item.get("file_url", ""),
        "thumbnail_url": item.get("thumbnail_url", ""),
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "explanation": build_result_explanation(item, query_text=query_text, query_mode=query_mode),
    }
```

- [ ] **Step 4: Switch both search paths to use the shared serializer**

Replace the list comprehensions in `search_text()` and `search_image()` with this pattern:

```python
return [
    _serialize_ranked_result(item, query_text=query_text, query_mode="text")
    for item in ranked[:limit]
]
```

and:

```python
return [
    _serialize_ranked_result(item, query_text=None, query_mode="image")
    for item in ranked[:limit]
]
```

- [ ] **Step 5: Re-run the API tests and confirm they pass**

Run from `Semedia/`:

```powershell
docker compose --profile test run --rm --build service-tests pytest testing/services/test_search_api.py -v
```

Expected: PASS for the two new payload tests and the existing search API tests.

---

### Task 3: Extend frontend types and render the explanation UI in result cards

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/components/SearchResultCard.tsx`
- Create: `frontend/src/components/SearchResultCard.test.tsx`

- [ ] **Step 1: Add a failing frontend rendering test**

Create `frontend/src/components/SearchResultCard.test.tsx` with this content:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { SearchResultCard } from './SearchResultCard'
import type { SearchResult } from '../types/api'

const onOpenMedia = vi.fn()

const textResult: SearchResult = {
  media_id: 1,
  scene_id: null,
  media_type: 'image',
  result_type: 'image',
  original_filename: 'office.jpg',
  score: 0.59,
  vector_score: 0.3,
  keyword_score: 1.0,
  caption: 'office desk',
  file_url: '/media/office.jpg',
  thumbnail_url: '/media/office.jpg',
  start_time: null,
  end_time: null,
  explanation: {
    match_type: 'caption',
    exact_phrase_match: true,
    rich_caption: false,
    rerank_boost: 0.08,
  },
}

const imageResult: SearchResult = {
  media_id: 2,
  scene_id: null,
  media_type: 'image',
  result_type: 'image',
  original_filename: 'red.jpg',
  score: 0.9,
  vector_score: 0.9,
  keyword_score: 0.0,
  caption: 'a red square',
  file_url: '/media/red.jpg',
  thumbnail_url: '/media/red.jpg',
  start_time: null,
  end_time: null,
  explanation: {
    match_type: 'visual',
    exact_phrase_match: false,
    rich_caption: false,
    rerank_boost: 0.0,
  },
}

describe('SearchResultCard explanations', () => {
  it('renders a compact explanation summary and score breakdown', () => {
    render(<SearchResultCard item={textResult} onOpenMedia={onOpenMedia} />)

    expect(screen.getByText('Caption match · exact phrase in caption')).toBeInTheDocument()
    expect(screen.getByText('Semantic 30%')).toBeInTheDocument()
    expect(screen.getByText('Caption 100%')).toBeInTheDocument()
    expect(screen.getByText('Boost +8%')).toBeInTheDocument()
  })

  it('hides the boost label when there is no rerank adjustment', () => {
    render(<SearchResultCard item={imageResult} onOpenMedia={onOpenMedia} />)

    expect(screen.getByText('Visual match')).toBeInTheDocument()
    expect(screen.getByText('Semantic 90%')).toBeInTheDocument()
    expect(screen.getByText('Caption 0%')).toBeInTheDocument()
    expect(screen.queryByText(/Boost \+/)).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the frontend test and confirm it fails**

Run from `Semedia/frontend/`:

```powershell
npm test -- src/components/SearchResultCard.test.tsx
```

Expected: FAIL because `SearchResult` does not yet include the new fields and the card does not render the explanation text.

- [ ] **Step 3: Extend the API types for richer search results**

Update `frontend/src/types/api.ts` so the search result contract matches the backend payload:

```ts
export interface SearchResultExplanation {
  match_type: 'visual' | 'caption' | 'hybrid'
  exact_phrase_match: boolean
  rich_caption: boolean
  rerank_boost: number
}

export interface SearchResult {
  media_id: number
  scene_id: number | null
  media_type: MediaType
  result_type: 'image' | 'video_scene'
  original_filename: string
  score: number
  vector_score: number
  keyword_score: number
  caption: string
  file_url: string
  thumbnail_url: string
  start_time: number | null
  end_time: number | null
  explanation: SearchResultExplanation
}
```

- [ ] **Step 4: Render the explanation summary and breakdown in `SearchResultCard.tsx`**

Add these small helpers above the component in `frontend/src/components/SearchResultCard.tsx`:

```tsx
function formatBoost(value: number): string {
  return `+${Math.round(value * 100)}%`
}

function getExplanationSummary(item: SearchResult): string {
  const matchTypeLabel = {
    visual: 'Visual match',
    caption: 'Caption match',
    hybrid: 'Hybrid match',
  }[item.explanation.match_type]

  const reasons: string[] = []
  if (item.explanation.exact_phrase_match) {
    reasons.push('exact phrase in caption')
  }
  if (item.explanation.rich_caption) {
    reasons.push('rich caption')
  }

  return reasons.length > 0 ? `${matchTypeLabel} · ${reasons.join(' · ')}` : matchTypeLabel
}
```

Then render the new block under the existing caption paragraph:

```tsx
<div className="space-y-1">
  {item.caption && (
    <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
      {item.caption}
    </p>
  )}

  <div className="space-y-1 text-xs text-muted-foreground">
    <p>{getExplanationSummary(item)}</p>
    <div className="flex flex-wrap gap-x-3 gap-y-1">
      <span>Semantic {formatScore(item.vector_score)}</span>
      <span>Caption {formatScore(item.keyword_score)}</span>
      {item.explanation.rerank_boost > 0 && (
        <span>Boost {formatBoost(item.explanation.rerank_boost)}</span>
      )}
    </div>
  </div>
</div>
```

This replaces the old standalone caption block with one grouped content section; do not change the thumbnail, score chip, or open-media behavior.

- [ ] **Step 5: Re-run the frontend test and confirm it passes**

Run from `Semedia/frontend/`:

```powershell
npm test -- src/components/SearchResultCard.test.tsx
```

Expected: PASS for both explanation rendering tests.

- [ ] **Step 6: Run the full frontend build**

Run from `Semedia/frontend/`:

```powershell
npm run build
```

Expected: PASS with a successful Vite production build.

---

### Task 4: Run cross-stack verification and manually inspect the UI

**Files:**
- No code changes in this task

- [ ] **Step 1: Run the backend verification set**

Run from `Semedia/`:

```powershell
docker compose --profile test run --rm --build service-tests pytest testing/services/test_ranking_service.py testing/services/test_search_api.py -v
```

Expected: PASS for all ranking and search API tests.

- [ ] **Step 2: Start the app stack with the updated frontend bundle**

Run from `Semedia/`:

```powershell
docker compose up --build -d gateway-api frontend
```

Expected: both services restart successfully and the frontend serves the new bundle.

- [ ] **Step 3: Manually verify one text result card and one image result card**

Use the running app in a browser:
- Visit `http://127.0.0.1:4173`
- Run a text query such as `dog` or `office desk`
- Confirm each result card shows:
  - the existing main relevance badge
  - a one-line explanation summary (`Caption match`, `Hybrid match`, or `Visual match`)
  - a breakdown row with `Semantic`, `Caption`, and optional `Boost`
- Run an image search with a smoke asset
- Confirm image-query results show `Visual match` and omit the boost label when `rerank_boost` is `0.0`

- [ ] **Step 4: Sanity-check the network payload in DevTools**

Open the browser Network panel and confirm the search response now includes these fields on each result object:

```json
{
  "scene_id": null,
  "vector_score": 0.3,
  "keyword_score": 1.0,
  "explanation": {
    "match_type": "caption",
    "exact_phrase_match": true,
    "rich_caption": false,
    "rerank_boost": 0.08
  }
}
```

Expected: frontend rendering matches the raw response payload.

---

## Done Criteria

This plan is complete when all of the following are true:
- `ranking_service.py` exposes `build_result_explanation()` and its unit tests pass.
- `search_service.py` returns `scene_id`, `vector_score`, `keyword_score`, and `explanation` for both text and image results.
- `SearchResultCard.tsx` shows a compact explanation summary and score breakdown without changing existing click behavior.
- `SearchResultCard.test.tsx` passes.
- `test_ranking_service.py` and `test_search_api.py` pass together in Docker.
- The updated frontend bundle is manually verified in the browser against the live stack.
