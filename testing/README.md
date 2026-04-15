# Testing

Automated tests for the new `Semedia/` application live here instead of inside the app package so the suite stays isolated from production modules.

## Layout

- `services/` contains active `gateway-api`, `media-worker`, and `search-api` tests for `Semedia/services/`
- `smoke-assets/` contains tiny image and video inputs used by the end-to-end smoke check

## Run

Run the active service tests from `Semedia/` with Docker Compose:

```bash
docker compose --profile test run --rm service-tests
```

Run the full-stack smoke test from the repository root:

```bash
python Semedia/testing/smoke_stack.py
```

The smoke test checks the frontend entrypoint, gateway health/runtime, image upload, video upload, search, and delete against the live Docker stack.
