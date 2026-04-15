# Semedia Frontend

This frontend is the active React + TypeScript client for the rebuilt semantic media search app in `Semedia/`.

## What It Covers

- upload dashboard for images and videos
- queue and recent-media visibility
- text search against the current backend
- media detail view with image preview or video scene navigation
- runtime badge for the strict CUDA backend

## Run Locally

```bash
cd Semedia/frontend
copy .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` if your backend is not running on `http://127.0.0.1:8000`.

## Validation

```bash
npm run lint
npm run build
```

The frontend expects the current `gateway-api` service on `http://127.0.0.1:8000`, not the old prototype in `SemaMedia-prev/`.
