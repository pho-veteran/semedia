# Frontend Implementation Guide

## Goal
Build a small but production-shaped frontend for the current service-based MVP in `Semedia/services/`. The frontend should cover upload, processing visibility, search, and result inspection without depending on legacy code in `SemaMedia-prev/`.

## Recommended Stack
- React + Vite + TypeScript
- React Router for page routing
- TanStack Query for API state, polling, and cache invalidation
- Axios or `fetch` wrapper for HTTP calls
- Vitest + Testing Library for component tests

Bootstrap target:

```bash
cd Semedia
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-router-dom @tanstack/react-query axios zod
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event msw
```

## App Structure

```text
Semedia/frontend/
  src/
    app/
    api/
    components/
    features/
      upload/
      media/
      search/
      runtime/
    pages/
    routes/
    types/
    utils/
```

## Routes
- `/`: dashboard with runtime status, recent uploads, and upload form
- `/search`: text query page with ranked results
- `/media/:id`: detail page with image preview or video scene list

## Backend Contracts
- `GET /api/v1/health/`: basic API liveness
- `GET /api/v1/runtime/`: CUDA/runtime status for a small system badge
- `POST /api/v1/media/upload/`: multipart upload, returns created media plus dispatch metadata
- `GET /api/v1/media/`: paginated media list with `count`, `next`, `previous`, `results`
- `GET /api/v1/media/{id}/`: media detail plus `scenes[]`
- `DELETE /api/v1/media/{id}/`: remove media and generated assets
- `POST /api/v1/search/`: `{ query_text, top_k? }` and ranked `results[]`

Use absolute backend base URL from `VITE_API_BASE_URL`, for example `http://127.0.0.1:8000`.

## UI Behavior
- Upload should accept image and video files and show immediate status from the upload response.
- Even though the current backend often runs sync, the UI should support polling detail until status is `completed` or `failed`.
- Search results should render two cards:
  - image result: thumbnail, filename, caption, score
  - video scene result: thumbnail, filename, scene time range, caption, score
- Video results should open an internal viewer and seek to `start_time` with an HTML5 `<video>` element. Do not rely only on raw `#t=` links.
- Failed items must show `error_message` from detail view.

## Implementation Order
1. Create app shell, router, API client, and shared types.
2. Build dashboard upload flow and recent media list.
3. Add media detail page with polling and delete action.
4. Build search page and result cards.
5. Add runtime status badge and empty/error states.
6. Add tests for upload, polling, search, and video seek behavior.

## Testing Targets
- Upload success and validation errors
- Polling stops on terminal media status
- Search renders image and video-scene results correctly
- Video viewer seeks to requested scene start time
- Delete removes item from cached lists and detail view
