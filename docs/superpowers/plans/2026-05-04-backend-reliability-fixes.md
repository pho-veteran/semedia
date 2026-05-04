# Backend Reliability Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the Semedia backend against invalid input, DB/filesystem divergence, fragile processing paths, and missing recovery tooling without adding new infrastructure.

**Architecture:** Keep the current gateway/search/worker split and make the existing flows safer. Fix public boundary validation first, then transactional sequencing, then processing invariants, then recovery utilities. Prefer small helper functions inside existing modules over new subsystems.

**Tech Stack:** FastAPI, SQLAlchemy ORM, pytest, Docker Compose, local filesystem storage, SQLite test fixtures

**Git note:** This Claude session is not inside a git repository, and the user wants commits to stay user-controlled. This plan omits commit steps.

---

## File Structure

### Existing files to modify
- `services/gateway_api/app/main.py` — upload validation, upload rollback cleanup, delete sequencing helpers
- `services/search_api/app/main.py` — positive-integer `top_k` validation helper
- `services/media_worker/app/main.py` — keep endpoint shape stable while relying on safer pipeline return values
- `services/shared/semedia_shared/search_service.py` — stable `scene_key` generation
- `services/shared/semedia_shared/pipeline.py` — missing-media handling, scene-output validation, safe scene replacement, derived-file cleanup
- `services/shared/semedia_shared/storage.py` — small helpers for deleting a single relative path and batches of relative paths safely
- `services/shared/semedia_shared/reprocess.py` — recovery utilities for stuck media, storage consistency scanning, and keyword-index rebuild
- `testing/services/test_gateway_api.py` — gateway validation and DB/filesystem consistency tests
- `testing/services/test_search_api.py` — `top_k` validation and `scene_key` stability tests
- `testing/services/test_media_worker_api.py` — worker endpoint behavior for missing media
- `testing/services/test_media_worker_pipeline.py` — safe reprocessing and mismatch handling tests

### New files to create
- `testing/services/test_reprocess.py` — tests for stuck-media detection, storage consistency scanning, and keyword-index repair helpers

### Responsibility boundaries
- `gateway_api` owns HTTP 422 behavior and safe sequencing around DB commit vs file deletion.
- `search_api` owns boundary validation of `top_k` before shared search code runs.
- `pipeline.py` owns all processing invariants and must never destroy a last-known-good scene set before a replacement is fully validated.
- `reprocess.py` owns operator-facing recovery utilities; it should not know HTTP details.

## Task 1: Fix boundary validation and stable scene identity

**Files:**
- Modify: `services/gateway_api/app/main.py`
- Modify: `services/search_api/app/main.py`
- Modify: `services/shared/semedia_shared/search_service.py`
- Test: `testing/services/test_gateway_api.py`
- Test: `testing/services/test_search_api.py`

- [ ] **Step 1: Write the failing tests for upload 422, positive `top_k`, and stable `scene_key`**

Add these tests to `testing/services/test_gateway_api.py` and `testing/services/test_search_api.py`:

```python
# testing/services/test_gateway_api.py

def test_upload_media_rejects_unsupported_media_type(gateway_env):
    response = gateway_env["client"].post(
        "/api/v1/media/upload/",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422
    assert "Unsupported media type" in response.json()["detail"]
```

```python
# testing/services/test_search_api.py

def test_search_rejects_zero_top_k(search_env):
    response = search_env["client"].post("/api/v1/search/", json={"query_text": "cat", "top_k": 0})

    assert response.status_code == 422
    assert response.json()["detail"] == "top_k must be greater than 0."


def test_search_rejects_negative_top_k(search_env):
    response = search_env["client"].post("/api/v1/search/", json={"query_text": "cat", "top_k": -5})

    assert response.status_code == 422
    assert response.json()["detail"] == "top_k must be greater than 0."
```

```python
# testing/services/test_search_api.py

def test_video_scene_results_use_stable_scene_keys(search_env, monkeypatch):
    module = search_env["module"]
    client = search_env["client"]
    session_factory = search_env["session_factory"]

    with session_factory() as session:
        video = MediaItem(
            file_path="originals/city.mp4",
            original_filename="duplicate-name.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=3,
            status=ProcessingStatus.COMPLETED,
            caption="",
            index_key="media:1",
        )
        session.add(video)
        session.commit()
        session.refresh(video)

        scene = VideoScene(
            media_id=video.id,
            scene_index=0,
            start_time=0.0,
            end_time=1.0,
            caption="blue city scene",
            embedding=[1.0, 0.0],
            keyframe_path="keyframes/1/scene_0000.jpg",
            thumbnail_path="thumbnails/1/scene_0000.jpg",
            index_key="scene:1:0",
        )
        session.add(scene)
        session.commit()
        session.refresh(scene)
        scene_id = scene.id

    monkeypatch.setattr(module, "_embed_image", lambda file: [1.0, 0.0])

    response = client.post(
        "/api/v1/search/by-image/",
        files={"file": ("query.png", VALID_PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["scene_key"] == f"scene:{scene_id}"
```

- [ ] **Step 2: Run the targeted tests and confirm they fail**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py::test_upload_media_rejects_unsupported_media_type testing/services/test_search_api.py::test_search_rejects_zero_top_k testing/services/test_search_api.py::test_search_rejects_negative_top_k testing/services/test_search_api.py::test_video_scene_results_use_stable_scene_keys -v
```

Expected:
- the upload test fails with 500/uncaught `ValueError`
- the `top_k` tests fail because the endpoint accepts `0` and negative values
- the `scene_key` test fails because the response uses filename-based keys

- [ ] **Step 3: Implement minimal boundary fixes**

Update `services/gateway_api/app/main.py` to convert invalid media-type inference into 422s:

```python
@app.post("/api/v1/media/upload/", status_code=status.HTTP_201_CREATED)
def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    media_type: str | None = Form(default=None),
    session: Session = Depends(get_db),
) -> dict:
    try:
        inferred_type = infer_media_type(file.filename or "upload.bin", file.content_type or "")
        if media_type:
            validate_media_type(media_type, inferred_type, file.filename or "upload.bin")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    selected_media_type = media_type or inferred_type
    ...
```

Add a positive-integer validator in `services/search_api/app/main.py` and use it in the text endpoint:

```python
def _coerce_positive_top_k(raw_top_k) -> int | None:
    if raw_top_k is None:
        return None
    try:
        top_k = int(raw_top_k)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="top_k must be an integer.") from exc
    if top_k <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="top_k must be greater than 0.")
    return top_k


@app.post("/api/v1/search/")
def search(payload: dict, session: Session = Depends(get_db)) -> dict:
    query_text = (payload.get("query_text") or "").strip()
    if not query_text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="query_text is required.")

    top_k = _coerce_positive_top_k(payload.get("top_k"))
    query_embedding = _embed_text(query_text)
    results = search_text(settings, session, query_text, query_embedding, top_k=top_k)
    return {"query_mode": "text", "query_text": query_text, "count": len(results), "results": results}
```

Use the same helper in the image endpoint by changing the form parameter type to `str | None` and validating it explicitly:

```python
@app.post("/api/v1/search/by-image/")
def search_by_image(
    file: UploadFile = File(...),
    top_k: str | None = Form(default=None),
    session: Session = Depends(get_db),
) -> dict:
    ...
    validated_top_k = _coerce_positive_top_k(top_k)
    query_embedding = _embed_image(file)
    results = search_image(settings, session, query_embedding, top_k=validated_top_k)
    ...
```

Update `services/shared/semedia_shared/search_service.py` so `scene_key` uses durable IDs:

```python
def _stable_scene_key(item: dict) -> str | None:
    scene_id = item.get("scene_id")
    if scene_id is None:
        return None
    return f"scene:{scene_id}"
```

- [ ] **Step 4: Run the targeted tests again and confirm they pass**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py::test_upload_media_rejects_unsupported_media_type testing/services/test_search_api.py::test_search_rejects_zero_top_k testing/services/test_search_api.py::test_search_rejects_negative_top_k testing/services/test_search_api.py::test_video_scene_results_use_stable_scene_keys -v
```

Expected:
- all four tests PASS

- [ ] **Step 5: Run adjacent regression tests for existing search/upload behavior**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py::test_upload_media_creates_record_and_dispatches_worker testing/services/test_search_api.py::test_search_requires_integer_top_k testing/services/test_search_api.py::test_image_search_returns_ranked_results -v
```

Expected:
- all tests PASS
- existing upload/search happy paths remain unchanged

### Task 2: Harden upload rollback and delete sequencing

**Files:**
- Modify: `services/gateway_api/app/main.py`
- Modify: `services/shared/semedia_shared/storage.py`
- Test: `testing/services/test_gateway_api.py`

- [ ] **Step 1: Write failing gateway consistency tests**

Add these tests to `testing/services/test_gateway_api.py`:

```python
def test_upload_media_cleans_saved_file_when_persist_fails(gateway_env, monkeypatch):
    module = gateway_env["module"]
    client = gateway_env["client"]
    settings = gateway_env["settings"]

    saved_path = settings.media_root / "originals" / "2026" / "05" / "04" / "broken.jpg"
    saved_path.parent.mkdir(parents=True, exist_ok=True)

    def fake_save_upload(settings, upload_file):
        saved_path.write_bytes(b"image-bytes")
        return "originals/2026/05/04/broken.jpg", len(b"image-bytes")

    monkeypatch.setattr(module, "save_upload", fake_save_upload)
    monkeypatch.setattr(module, "_persist_uploaded_media", lambda session, media: (_ for _ in ()).throw(RuntimeError("db write failed")))

    response = client.post(
        "/api/v1/media/upload/",
        files={"file": ("broken.jpg", b"image-bytes", "image/jpeg")},
    )

    assert response.status_code == 500
    assert not saved_path.exists()
```

```python
def test_delete_media_preserves_files_when_db_delete_fails(gateway_env, monkeypatch):
    module = gateway_env["module"]
    client = gateway_env["client"]
    settings = gateway_env["settings"]
    session_factory = gateway_env["session_factory"]

    media_dir = settings.media_root / "originals" / "2026" / "05" / "04"
    media_dir.mkdir(parents=True, exist_ok=True)
    media_file = media_dir / "sample.mp4"
    media_file.write_bytes(b"video")

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/2026/05/04/sample.mp4",
            original_filename="sample.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=5,
            status=ProcessingStatus.COMPLETED,
            index_key="media:1",
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        media_id = media.id

    monkeypatch.setattr(module, "_delete_media_row", lambda session, media: (_ for _ in ()).throw(RuntimeError("db delete failed")))

    response = client.delete(f"/api/v1/media/{media_id}/")

    assert response.status_code == 500
    assert media_file.exists()
```

- [ ] **Step 2: Run the targeted tests and confirm they fail**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py::test_upload_media_cleans_saved_file_when_persist_fails testing/services/test_gateway_api.py::test_delete_media_preserves_files_when_db_delete_fails -v
```

Expected:
- the upload rollback test fails because the saved file remains on disk
- the delete sequencing test fails because current code deletes files before the DB failure occurs

- [ ] **Step 3: Add small gateway helpers and implement rollback-safe sequencing**

Add focused helpers to `services/gateway_api/app/main.py`:

```python
def _persist_uploaded_media(session: Session, media: MediaItem) -> None:
    session.add(media)
    session.commit()
    session.refresh(media)


def _delete_media_row(session: Session, media: MediaItem) -> None:
    session.delete(media)
    session.commit()
```

Update upload handling to clean up the file if persistence fails:

```python
from semedia_shared.storage import delete_relative_path_if_exists

...
    relative_path, file_size = save_upload(settings, file)
    media = MediaItem(
        file_path=relative_path,
        original_filename=file.filename or "upload.bin",
        media_type=selected_media_type,
        mime_type=file.content_type or "",
        file_size=file_size,
        status=ProcessingStatus.PENDING,
        enqueued_at=datetime.now(timezone.utc),
    )
    try:
        _persist_uploaded_media(session, media)
    except Exception:
        session.rollback()
        delete_relative_path_if_exists(settings, relative_path)
        raise
```

Update delete handling to commit the DB delete before touching storage:

```python
def delete_media(media_id: int, session: Session = Depends(get_db)) -> None:
    media = session.execute(
        select(MediaItem).options(selectinload(MediaItem.scenes)).where(MediaItem.id == media_id)
    ).scalar_one_or_none()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")

    paths_to_delete = [media.file_path, *[scene.keyframe_path for scene in media.scenes], *[scene.thumbnail_path for scene in media.scenes]]
    _delete_media_row(session, media)
    delete_relative_paths_if_exist(settings, paths_to_delete)
    try:
        from semedia_shared.index_service import rebuild_keyword_index
        rebuild_keyword_index(settings, session)
    except Exception:
        logger.exception("Keyword index rebuild failed after deleting media %s", media_id)
```

Add small storage helpers in `services/shared/semedia_shared/storage.py`:

```python
def delete_relative_path_if_exists(settings, relative_path: str | None) -> None:
    if not relative_path:
        return
    delete_path_if_exists(resolve_media_path(settings, relative_path))


def delete_relative_paths_if_exist(settings, relative_paths: list[str | None]) -> None:
    for relative_path in relative_paths:
        delete_relative_path_if_exists(settings, relative_path)
```

- [ ] **Step 4: Run the targeted consistency tests again and confirm they pass**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py::test_upload_media_cleans_saved_file_when_persist_fails testing/services/test_gateway_api.py::test_delete_media_preserves_files_when_db_delete_fails -v
```

Expected:
- both tests PASS

- [ ] **Step 5: Re-run existing upload/delete regressions**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py::test_upload_media_creates_record_and_dispatches_worker testing/services/test_gateway_api.py::test_delete_media_removes_database_rows_and_files testing/services/test_gateway_api.py::test_delete_media_rebuilds_keyword_index_artifact -v
```

Expected:
- all tests PASS
- happy-path upload/delete behavior still works

### Task 3: Make missing-media processing safe and bounded

**Files:**
- Modify: `services/shared/semedia_shared/pipeline.py`
- Test: `testing/services/test_media_worker_api.py`
- Test: `testing/services/test_media_worker_pipeline.py`

- [ ] **Step 1: Write failing tests for missing media IDs**

Add these tests:

```python
# testing/services/test_media_worker_api.py

def test_worker_process_endpoint_returns_success_false_for_missing_media(worker_env):
    response = worker_env["client"].post("/internal/media/999/process")

    assert response.status_code == 200
    assert response.json() == {"media_id": 999, "success": False}
```

```python
# testing/services/test_media_worker_pipeline.py

def test_process_media_returns_false_when_media_row_is_missing(tmp_path, caplog):
    settings, engine, session_factory = _prepare_session(tmp_path)

    with session_factory() as session:
        with caplog.at_level(logging.WARNING):
            assert process_media(settings, session, 999) is False

    assert "Media 999 no longer exists" in caplog.text
    engine.dispose()
```

- [ ] **Step 2: Run the missing-media tests and confirm they fail**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_media_worker_api.py::test_worker_process_endpoint_returns_success_false_for_missing_media testing/services/test_media_worker_pipeline.py::test_process_media_returns_false_when_media_row_is_missing -v
```

Expected:
- the API test fails with a 500 path
- the pipeline test fails because `.scalar_one()` raises instead of returning `False`

- [ ] **Step 3: Change `process_media()` to use explicit missing-row handling**

Update `services/shared/semedia_shared/pipeline.py`:

```python
def process_media(settings, session: Session, media_id: int) -> bool:
    media = session.execute(
        select(MediaItem).options(selectinload(MediaItem.scenes)).where(MediaItem.id == media_id)
    ).scalar_one_or_none()
    if media is None:
        logger.warning("Media %s no longer exists; skipping processing.", media_id)
        return False

    logger.info("Processing started for media %s (%s).", media_id, media.media_type)
    media.status = ProcessingStatus.PROCESSING
    media.error_message = ""
    media.updated_at = datetime.now(timezone.utc)
    session.commit()
    ...
```

Do not change the worker endpoint shape in `services/media_worker/app/main.py`; it should continue returning:

```python
return {"media_id": media_id, "success": ok}
```

- [ ] **Step 4: Re-run the missing-media tests and confirm they pass**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_media_worker_api.py::test_worker_process_endpoint_returns_success_false_for_missing_media testing/services/test_media_worker_pipeline.py::test_process_media_returns_false_when_media_row_is_missing -v
```

Expected:
- both tests PASS

- [ ] **Step 5: Re-run the existing worker processing happy-path tests**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_media_worker_api.py::test_worker_process_endpoint_invokes_pipeline testing/services/test_media_worker_pipeline.py::test_process_media_image_populates_caption_and_embedding testing/services/test_media_worker_pipeline.py::test_process_media_marks_item_failed_when_pipeline_errors -v
```

Expected:
- all tests PASS

### Task 4: Protect video scene integrity during reprocessing

**Files:**
- Modify: `services/shared/semedia_shared/pipeline.py`
- Modify: `services/shared/semedia_shared/storage.py`
- Test: `testing/services/test_media_worker_pipeline.py`

- [ ] **Step 1: Write failing tests for mismatched outputs and last-known-good preservation**

Add these tests to `testing/services/test_media_worker_pipeline.py`:

```python
def test_process_media_video_preserves_existing_scenes_when_caption_count_is_short(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    (original_dir / "sample.mp4").write_bytes(b"video-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "get_video_duration", lambda path: 2.0)
    monkeypatch.setattr(
        pipeline_module,
        "detect_scenes",
        lambda settings, path: [
            SceneSpan(scene_index=0, start_time=0.0, end_time=1.0),
            SceneSpan(scene_index=1, start_time=1.0, end_time=2.0),
        ],
    )

    def fake_extract_single(settings, path, media_id, scene):
        keyframe_dir = settings.media_root / "keyframes" / str(media_id)
        thumbnail_dir = settings.media_root / "thumbnails" / str(media_id)
        keyframe_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        keyframe = keyframe_dir / f"scene_{scene.scene_index:04d}.jpg"
        thumbnail = thumbnail_dir / f"scene_{scene.scene_index:04d}.jpg"
        keyframe.write_bytes(b"frame")
        thumbnail.write_bytes(b"thumb")
        return str(keyframe), str(thumbnail)

    monkeypatch.setattr(pipeline_module, "extract_scene_keyframe", fake_extract_single)
    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["only one caption"])
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [[1.0, 0.0], [0.0, 1.0]])

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/sample.mp4",
            original_filename="sample.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=11,
            status=ProcessingStatus.COMPLETED,
            caption="old summary",
            index_key="media:1",
        )
        session.add(media)
        session.commit()
        session.refresh(media)

        session.add(
            VideoScene(
                media_id=media.id,
                scene_index=0,
                start_time=0.0,
                end_time=1.0,
                caption="old scene",
                embedding=[0.5, 0.5],
                keyframe_path=f"keyframes/{media.id}/scene_0000.jpg",
                thumbnail_path=f"thumbnails/{media.id}/scene_0000.jpg",
                index_key=f"scene:{media.id}:0",
            )
        )
        session.commit()

        assert process_media(settings, session, media.id) is False
        session.refresh(media)
        scenes = session.query(VideoScene).filter(VideoScene.media_id == media.id).order_by(VideoScene.scene_index).all()

        assert media.status == ProcessingStatus.FAILED
        assert "Expected 2 captions, got 1" in media.error_message
        assert len(scenes) == 1
        assert scenes[0].caption == "old scene"

    engine.dispose()
```

```python
def test_process_media_video_cleans_generated_files_when_replacement_fails(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    (original_dir / "sample.mp4").write_bytes(b"video-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "get_video_duration", lambda path: 2.0)
    monkeypatch.setattr(
        pipeline_module,
        "detect_scenes",
        lambda settings, path: [SceneSpan(scene_index=0, start_time=0.0, end_time=2.0)],
    )

    def fake_extract_single(settings, path, media_id, scene):
        keyframe_dir = settings.media_root / "keyframes" / str(media_id)
        thumbnail_dir = settings.media_root / "thumbnails" / str(media_id)
        keyframe_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        keyframe = keyframe_dir / "scene_0000.jpg"
        thumbnail = thumbnail_dir / "scene_0000.jpg"
        keyframe.write_bytes(b"frame")
        thumbnail.write_bytes(b"thumb")
        return str(keyframe), str(thumbnail)

    monkeypatch.setattr(pipeline_module, "extract_scene_keyframe", fake_extract_single)
    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["caption"])
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [])

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/sample.mp4",
            original_filename="sample.mp4",
            media_type="video",
            mime_type="video/mp4",
            file_size=11,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        media_id = media.id

        assert process_media(settings, session, media_id) is False

    assert not (settings.media_root / f"keyframes/{media_id}/scene_0000.jpg").exists()
    assert not (settings.media_root / f"thumbnails/{media_id}/scene_0000.jpg").exists()
    engine.dispose()
```

- [ ] **Step 2: Run the reprocessing integrity tests and confirm they fail**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_media_worker_pipeline.py::test_process_media_video_preserves_existing_scenes_when_caption_count_is_short testing/services/test_media_worker_pipeline.py::test_process_media_video_cleans_generated_files_when_replacement_fails -v
```

Expected:
- the preservation test fails because current code deletes old scenes too early
- the cleanup test fails because generated derived files remain after failure

- [ ] **Step 3: Refactor `_process_video()` to validate counts before replacement and clean generated files on failure**

Add small helpers in `services/shared/semedia_shared/pipeline.py`:

```python
def _validate_scene_outputs(scene_payloads: list[dict], captions: list[str], embeddings: list[list[float]]) -> None:
    expected_count = len(scene_payloads)
    if len(captions) != expected_count:
        raise ValueError(f"Expected {expected_count} captions, got {len(captions)}")
    if len(embeddings) != expected_count:
        raise ValueError(f"Expected {expected_count} embeddings, got {len(embeddings)}")


def _cleanup_generated_scene_files(settings, generated_paths: list[str]) -> None:
    for path_str in generated_paths:
        delete_path_if_exists(Path(path_str))
```

Refactor `_process_video()` so scene rows are replaced only after all new outputs are ready:

```python
def _process_video(settings, session: Session, media: MediaItem) -> None:
    video_path = str(settings.media_root / media.file_path)
    media.duration = get_video_duration(video_path)
    media.updated_at = datetime.now(timezone.utc)
    session.commit()

    scenes = detect_scenes(settings, video_path)
    if not scenes:
        raise ValueError("No scenes detected and video duration could not be determined.")

    generated_paths: list[str] = []
    scene_payloads: list[dict] = []
    for scene in scenes:
        keyframe_path, thumbnail_path = extract_scene_keyframe(settings, video_path, media.id, scene)
        generated_paths.extend([keyframe_path, thumbnail_path])
        scene_payloads.append(
            {
                "scene_index": scene.scene_index,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "keyframe_path": keyframe_path,
                "thumbnail_path": thumbnail_path,
            }
        )

    try:
        frame_paths = [payload["keyframe_path"] for payload in scene_payloads]
        captions = generate_captions(settings, frame_paths)
        embeddings = encode_images(settings, frame_paths)
        _validate_scene_outputs(scene_payloads, captions, embeddings)

        created_scenes = []
        for payload, caption, embedding in zip(scene_payloads, captions, embeddings):
            created_scenes.append(
                VideoScene(
                    media_id=media.id,
                    scene_index=payload["scene_index"],
                    start_time=payload["start_time"],
                    end_time=payload["end_time"],
                    keyframe_path=relative_to_media_root(settings, payload["keyframe_path"]),
                    thumbnail_path=relative_to_media_root(settings, payload["thumbnail_path"]),
                    caption=caption,
                    embedding=embedding,
                    index_key=f"scene:{media.id}:{payload['scene_index']}",
                )
            )

        for scene in list(media.scenes):
            session.delete(scene)
        session.flush()
        session.add_all(created_scenes)
        media.caption = _truncate_text(_join_unique_non_empty([scene.caption for scene in created_scenes], max_items=3), 200)
        media.index_key = f"media:{media.id}"
        media.updated_at = datetime.now(timezone.utc)
        session.commit()
    except Exception:
        session.rollback()
        _cleanup_generated_scene_files(settings, generated_paths)
        raise
```

Add the missing imports at the top of `pipeline.py`:

```python
from pathlib import Path
from .storage import delete_path_if_exists, relative_to_media_root
```

- [ ] **Step 4: Re-run the reprocessing integrity tests and confirm they pass**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_media_worker_pipeline.py::test_process_media_video_preserves_existing_scenes_when_caption_count_is_short testing/services/test_media_worker_pipeline.py::test_process_media_video_cleans_generated_files_when_replacement_fails -v
```

Expected:
- both tests PASS

- [ ] **Step 5: Run the existing video processing tests as regressions**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_media_worker_pipeline.py::test_process_media_video_uses_single_frame_extraction testing/services/test_media_worker_pipeline.py::test_process_video_flags_duplicate_adjacent_captions testing/services/test_media_worker_pipeline.py::test_process_media_video_rebuilds_keyword_index_with_new_scenes -v
```

Expected:
- all tests PASS

### Task 5: Add callable recovery utilities for stuck media, storage consistency, and index repair

**Files:**
- Modify: `services/shared/semedia_shared/reprocess.py`
- Modify: `services/shared/semedia_shared/storage.py`
- Create: `testing/services/test_reprocess.py`

- [ ] **Step 1: Write the failing recovery tests**

Create `testing/services/test_reprocess.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from semedia_shared.models import MediaItem, ProcessingStatus
from semedia_shared.pipeline import process_media
from semedia_shared.reprocess import find_stuck_media, rebuild_keyword_index_repair, scan_storage_consistency

from .test_media_worker_pipeline import _prepare_session


def test_find_stuck_media_returns_old_pending_and_processing_items(tmp_path):
    settings, engine, session_factory = _prepare_session(tmp_path)
    now = datetime.now(timezone.utc)

    with session_factory() as session:
        session.add_all(
            [
                MediaItem(
                    file_path="originals/pending.jpg",
                    original_filename="pending.jpg",
                    media_type="image",
                    mime_type="image/jpeg",
                    file_size=1,
                    status=ProcessingStatus.PENDING,
                    enqueued_at=now - timedelta(hours=2),
                ),
                MediaItem(
                    file_path="originals/processing.jpg",
                    original_filename="processing.jpg",
                    media_type="image",
                    mime_type="image/jpeg",
                    file_size=1,
                    status=ProcessingStatus.PROCESSING,
                    enqueued_at=now - timedelta(hours=3),
                    updated_at=now - timedelta(hours=2),
                ),
            ]
        )
        session.commit()

        stuck = find_stuck_media(session, now=now, pending_after=timedelta(minutes=30), processing_after=timedelta(minutes=30))

    assert {item["status"] for item in stuck} == {ProcessingStatus.PENDING, ProcessingStatus.PROCESSING}
    engine.dispose()


def test_scan_storage_consistency_reports_orphans_and_missing_files(tmp_path):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    orphan_path = original_dir / "orphan.jpg"
    orphan_path.write_bytes(b"orphan")

    with session_factory() as session:
        session.add(
            MediaItem(
                file_path="originals/missing.jpg",
                original_filename="missing.jpg",
                media_type="image",
                mime_type="image/jpeg",
                file_size=1,
                status=ProcessingStatus.COMPLETED,
            )
        )
        session.commit()

        report = scan_storage_consistency(settings, session)

    assert "originals/orphan.jpg" in report["orphaned_original_files"]
    assert any(item["file_path"] == "originals/missing.jpg" for item in report["missing_media_files"])
    engine.dispose()


def test_rebuild_keyword_index_repair_rebuilds_current_artifact(tmp_path, monkeypatch):
    settings, engine, session_factory = _prepare_session(tmp_path)
    original_dir = settings.media_root / "originals"
    original_dir.mkdir(parents=True, exist_ok=True)
    (original_dir / "cat.jpg").write_bytes(b"image-bytes")

    from semedia_shared import pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "generate_captions", lambda settings, paths: ["cat on sofa"])
    monkeypatch.setattr(pipeline_module, "encode_images", lambda settings, paths: [[0.1, 0.2, 0.3]])

    with session_factory() as session:
        media = MediaItem(
            file_path="originals/cat.jpg",
            original_filename="cat.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=11,
            status=ProcessingStatus.PENDING,
        )
        session.add(media)
        session.commit()
        session.refresh(media)
        assert process_media(settings, session, media.id) is True

        document_count = rebuild_keyword_index_repair(settings, session)

    assert document_count == 1
    engine.dispose()
```

- [ ] **Step 2: Run the new recovery tests and confirm they fail**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_reprocess.py -v
```

Expected:
- import errors or attribute errors because the recovery utilities do not exist yet

- [ ] **Step 3: Implement the callable recovery utilities in `reprocess.py`**

Fill `services/shared/semedia_shared/reprocess.py` with small, focused helpers:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .index_service import rebuild_keyword_index
from .models import MediaItem, ProcessingStatus, VideoScene


def find_stuck_media(
    session: Session,
    *,
    now: datetime | None = None,
    pending_after: timedelta = timedelta(minutes=30),
    processing_after: timedelta = timedelta(hours=1),
) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    items = session.execute(select(MediaItem)).scalars().all()
    stuck: list[dict] = []
    for media in items:
        if media.status == ProcessingStatus.PENDING and media.enqueued_at and now - media.enqueued_at > pending_after:
            stuck.append({"media_id": media.id, "status": media.status, "reason": "pending_timeout"})
        elif media.status == ProcessingStatus.PROCESSING and media.updated_at and now - media.updated_at > processing_after:
            stuck.append({"media_id": media.id, "status": media.status, "reason": "processing_timeout"})
    return stuck


def scan_storage_consistency(settings, session: Session) -> dict:
    media_rows = session.execute(select(MediaItem).options(selectinload(MediaItem.scenes))).scalars().all()
    known_originals = {media.file_path for media in media_rows if media.file_path}
    orphaned_original_files: list[str] = []
    originals_root = settings.media_root / "originals"
    if originals_root.exists():
        for path in originals_root.rglob("*"):
            if path.is_file():
                relative_path = str(path.relative_to(settings.media_root)).replace("\\", "/")
                if relative_path not in known_originals:
                    orphaned_original_files.append(relative_path)

    missing_media_files = [
        {"media_id": media.id, "file_path": media.file_path}
        for media in media_rows
        if media.file_path and not (settings.media_root / media.file_path).exists()
    ]
    missing_scene_files = [
        {"scene_id": scene.id, "path": path}
        for media in media_rows
        for scene in media.scenes
        for path in [scene.keyframe_path, scene.thumbnail_path]
        if path and not (settings.media_root / path).exists()
    ]

    return {
        "orphaned_original_files": sorted(orphaned_original_files),
        "missing_media_files": missing_media_files,
        "missing_scene_files": missing_scene_files,
    }


def rebuild_keyword_index_repair(settings, session: Session) -> int:
    rebuild_keyword_index(settings, session)
    media_rows = session.execute(select(MediaItem).where(MediaItem.status == ProcessingStatus.COMPLETED)).scalars().all()
    scene_rows = session.execute(select(VideoScene)).scalars().all()
    return sum(1 for media in media_rows if media.media_type == "image" and media.caption) + sum(1 for scene in scene_rows if scene.caption)
```

- [ ] **Step 4: Run the new recovery tests again and confirm they pass**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_reprocess.py -v
```

Expected:
- all recovery tests PASS

- [ ] **Step 5: Run the broader reliability subset including recovery and pipeline tests**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py testing/services/test_search_api.py testing/services/test_media_worker_api.py testing/services/test_media_worker_pipeline.py testing/services/test_reprocess.py -v
```

Expected:
- the full backend reliability subset PASSes

### Task 6: Final verification

**Files:**
- Modify: none
- Test: `testing/services/test_gateway_api.py`
- Test: `testing/services/test_search_api.py`
- Test: `testing/services/test_media_worker_api.py`
- Test: `testing/services/test_media_worker_pipeline.py`
- Test: `testing/services/test_reprocess.py`

- [ ] **Step 1: Run the full backend service suite**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm --build service-tests
```

Expected:
- all backend service tests PASS

- [ ] **Step 2: Re-run the smoke-critical API subset**

Run from `Semedia/`:

```bash
docker compose --profile test run --rm service-tests pytest testing/services/test_gateway_api.py::test_upload_media_creates_record_and_dispatches_worker testing/services/test_gateway_api.py::test_delete_media_removes_database_rows_and_files testing/services/test_search_api.py::test_search_returns_ranked_results testing/services/test_media_worker_api.py::test_worker_process_endpoint_invokes_pipeline -v
```

Expected:
- all smoke-critical API tests PASS

- [ ] **Step 3: Review whether any docs need updates**

Check these files for required updates:

```text
- docs/superpowers/specs/2026-05-03-backend-reliability-fixes-design.md
- docs/TASKS.md
- docs/metrics/search_quality_history.md
```

Expected decision:
- no metrics-history change unless result semantics changed beyond validation and stable IDs
- no plan/task updates unless implementation scope changed materially during execution

- [ ] **Step 4: Record final manual verification notes in the PR/summary, not in new docs**

Use this checklist:

```text
- invalid upload type now returns 422
- top_k <= 0 now returns 422
- upload DB failure cleans up saved file
- delete DB failure does not remove files prematurely
- missing media processing returns success=false without crashing
- video reprocessing preserves last-known-good scenes on mismatch
- recovery utilities detect stuck media and storage inconsistencies
```

Expected:
- all checklist items confirmed by tests

- [ ] **Step 5: Stop and ask the user before any commit or branch-integration action**

Use this message:

```text
Implementation complete and verified locally. I have not created any git commit. If you want, I can now prepare a commit message or help review the diff.
```

Expected:
- no autonomous commit or branch action

## Self-review checklist

### Spec coverage
- boundary validation: covered by Task 1
- upload/delete consistency: covered by Task 2
- missing-media safety and worker bounded behavior: covered by Task 3
- safe scene replacement and derived-file cleanup: covered by Task 4
- recovery utilities for stuck media, storage consistency, and index repair: covered by Task 5
- full verification and no autonomous commit: covered by Task 6

### Placeholder scan
- No `TODO`, `TBD`, or "similar to above" references remain.
- Each code-changing step includes concrete code blocks.
- Each verification step includes an exact Docker test command and expected outcome.

### Type consistency
- `top_k` validator returns `int | None`
- `scene_key` uses `scene:{scene_id}` consistently
- recovery helpers live in `reprocess.py`
- gateway sequencing helpers are `_persist_uploaded_media()` and `_delete_media_row()` consistently across tests and implementation
