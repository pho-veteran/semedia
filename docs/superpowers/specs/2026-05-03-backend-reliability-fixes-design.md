# Backend Reliability Fixes Design

**Date:** 2026-05-03  
**Author:** Claude Code  
**Status:** Draft for review

## 1. Summary

This design hardens the current Semedia backend against confirmed correctness and reliability failures without introducing new infrastructure or materially changing the public API surface.

The work focuses on five outcomes:
- reject invalid boundary inputs consistently
- prevent new database/filesystem divergence during upload and delete flows
- make media processing failures explicit, bounded, and recoverable
- preserve indexed scene integrity during video processing and reprocessing
- add maintenance paths to detect and repair already-bad state in existing environments

This is a broad cleanup inside the existing service layout, not a queue-system redesign.

## 2. Goals

- Fix the confirmed backend bugs found in the audit.
- Preserve current public gateway/search API payload shapes where possible.
- Improve correctness first, then improve recoverability for partial-failure paths.
- Keep the current service topology and avoid adding an external queue, broker, or new always-on subsystem.
- Add recovery tools for orphaned files, stuck media states, and keyword-index resync.

## 3. Non-goals

- Introduce Redis, Celery, Kafka, or another external job system.
- Redesign the search/ranking architecture.
- Change accepted public request/response shapes beyond targeted validation behavior.
- Replace the current keyword index architecture.
- Perform unrelated refactoring outside the affected backend paths.

## 4. Confirmed Problems in Scope

### 4.1 Input validation and API semantics
- Invalid upload media types can escape as unhandled `ValueError` failures instead of consistent 4xx responses.
- `top_k` accepts invalid values such as `0` or negatives and falls back or slices unexpectedly.

### 4.2 Database/filesystem consistency
- Upload saves a file before the database row is durable, with no rollback cleanup on DB failure.
- Delete removes files before the database deletion is committed, allowing DB/file divergence.

### 4.3 Processing reliability and failure signaling
- Background dispatch is process-local and not durable by itself.
- Worker processing can fail ambiguously from the caller’s perspective.
- Missing media rows can crash processing due to unchecked `.scalar_one()` assumptions.

### 4.4 Scene integrity and partial failure
- Video reprocessing deletes prior scenes before new scene creation is fully validated.
- Scene creation currently trusts caption/embedding batch lengths and can silently truncate if they diverge.

### 4.5 Search/result identity and recovery gaps
- `scene_key` is not globally unique when derived from original filename plus scene index.
- There is no explicit built-in maintenance path for stuck media, orphaned files, or keyword-index resync.

## 5. Constraints

- **Infrastructure constraint:** no new infrastructure. Use the existing FastAPI services, database, and media storage only.
- **Compatibility constraint:** preserve current public API shapes and minimize client-visible changes.
- **Recovery constraint:** include remediation for already-bad state, not only prevention of future issues.
- **Workflow constraint:** prefer local, surgical changes over introducing new abstractions.

## 6. Design Overview

The design keeps the current three-service architecture:
- `gateway_api` remains the public entrypoint for upload, delete, and search proxying.
- `media_worker` remains responsible for processing and embedding generation.
- `search_api` remains responsible for search validation and retrieval.
- shared logic under `semedia_shared` remains the place for pipeline, storage, indexing, and serialization behavior.

The implementation will harden existing boundaries rather than add a new subsystem. Reliability comes from better sequencing, stronger invariants, and explicit recovery utilities backed by the existing database and media storage.

## 7. Detailed Design

### 7.1 Input validation and public API behavior

#### Invalid media type handling
`gateway_api/app/main.py` will catch `ValueError` from `infer_media_type()` and `validate_media_type()` and convert those failures into HTTP 422 responses.

This aligns upload behavior with the stricter handling already used in search/image endpoints while preserving the endpoint shape.

#### `top_k` validation
`search_api/app/main.py` will treat `top_k` as valid only when it is a positive integer.

Rules:
- omitted `top_k` keeps current default behavior
- non-integer `top_k` returns 422
- `top_k <= 0` returns 422

This removes the current `top_k or settings.search_max_results` ambiguity where `0` silently becomes the default and negatives can affect slicing in surprising ways.

### 7.2 Upload flow hardening

Current behavior writes the uploaded file first and persists the DB row second. The fix keeps that basic shape but adds rollback cleanup.

New behavior:
1. save file to storage
2. attempt DB insert + commit
3. if commit succeeds, continue normally
4. if commit fails, delete the just-written file, rollback the session, and surface the failure

This prevents new orphaned upload files from DB-write failures without changing the endpoint contract.

### 7.3 Delete flow hardening

Current behavior deletes storage assets before the DB delete is durable. That makes filesystem state lead the source-of-truth row state.

New behavior:
1. load the media row and record the file paths that must be deleted
2. delete the DB row and commit first
3. after commit succeeds, delete the recorded files from storage
4. if post-commit file deletion partially fails, log the failure and leave it for maintenance cleanup
5. attempt keyword-index rebuild after the delete commit; if it fails, log and leave it repairable through maintenance

This favors database truth over immediate storage cleanup. It can leave temporary orphaned files after a post-commit deletion failure, but it avoids the more damaging case where the DB points at already-missing files after a rollback.

### 7.4 Processing failure signaling and missing-row safety

#### Missing media safety
`process_media()` will stop assuming the target row always exists. Missing rows will be handled explicitly and return a controlled failure result instead of allowing an uncaught ORM exception to escape.

Expected behavior:
- if the media row is missing before processing starts, log a bounded warning and return failure
- do not create a new exception path that turns a missing row into an unexpected 500 crash

#### Worker failure semantics
The gateway will continue to treat transport-level failure as dispatch failure, preserving compatibility. Internally, processing failure will remain persisted on the media row with explicit `FAILED` status and `error_message`.

The worker endpoint will be made less ambiguous by ensuring that a failed processing run is clearly represented in persistent state and can be distinguished from a dispatch failure or a never-started task.

### 7.5 Background-processing recoverability without new infrastructure

`BackgroundTasks` will remain in place, but the system will stop assuming it provides sufficient durability.

Design additions:
- define stuck-state heuristics for `PENDING` and `PROCESSING` media based on persisted timestamps
- add recovery utilities that can detect media items that were enqueued but never completed
- allow those utilities to either re-dispatch processing or mark items failed with an explicit diagnostic message, depending on the detected state

This does not create a new queue. It makes the existing best-effort dispatch recoverable using persisted state.

### 7.6 Video processing invariants and safe scene replacement

This is the most important correctness area after boundary validation.

#### Batch-length validation
Before creating or replacing scene rows, the pipeline will verify that:
- detected scene count
- generated caption count
- generated embedding count

all match exactly.

If they do not match, processing fails explicitly and no partial scene replacement is committed.

#### Safe scene replacement
Current behavior deletes old scenes before all new outputs are safely ready. The replacement strategy will change to protect the last known-good indexed scene set.

Target behavior:
1. detect scenes
2. extract keyframes/thumbnails
3. generate captions and embeddings
4. validate all counts and required payloads
5. only after the full new scene set is ready, replace the existing scene rows in one bounded update path

The design goal is: **processing failure must not silently destroy a previously valid scene set**.

The implementation may still use multiple commits internally where necessary, but the visible state transition must preserve either the old valid scene set or a fully validated new one.

#### Derived file cleanup on processing failure
If video processing creates new keyframes/thumbnails and later fails before replacement completes, those derived files must be cleaned up or left in a state that the maintenance utility can deterministically remove.

### 7.7 Stable search result identity

`scene_key` will stop using `original_filename + scene_index` and instead use stable database-backed identity.

Preferred format:
- `scene:{scene_id}` when `scene_id` exists

If a slightly richer format is preferred for debugging, `scene:{media_id}:{scene_id}` is also acceptable, but uniqueness must come from durable IDs rather than user-controlled filenames.

This change preserves the presence of `scene_key` in responses while making it globally unique and stable across duplicate filenames.

### 7.8 Keyword-index integrity and maintenance

The current keyword-index architecture stays in place. This work does not redesign it.

Hardening additions:
- keep rebuild hooks after successful processing and delete flows
- add an explicit maintenance path to rebuild/resync the keyword index on demand
- treat rebuild failure as repairable operational state rather than silent drift

The cache remains process-local, but index state becomes easier to restore intentionally when drift or deserialization issues occur.

### 7.9 Maintenance and recovery utilities

Add internal maintenance entrypoints or callable utilities under the existing backend codebase for three classes of repair.

#### Media-state recovery
Detect and report media items that are:
- stuck in `PENDING` beyond the expected enqueue window
- stuck in `PROCESSING` beyond the expected processing window
- marked `FAILED` with recoverable causes

Supported actions:
- mark failed with explicit recovery note
- re-dispatch processing when safe

#### Storage consistency recovery
Detect and report:
- orphaned original uploads with no backing DB row
- orphaned derived files with no backing scene row
- DB rows that reference missing original files
- scene rows that reference missing keyframe/thumbnail files

Supported actions:
- delete true orphans from storage
- mark affected DB rows failed or degraded with explicit diagnostics

#### Keyword-index recovery
Support explicit rebuild/resync of the durable keyword index artifact from current completed media/scenes.

These tools may be implemented as internal endpoints, scripts, or callable service utilities, but they must remain inside the existing project and not depend on new infrastructure.

## 8. File-Level Change Plan

### `services/gateway_api/app/main.py`
- catch upload media-type `ValueError` and return 422
- add safer upload cleanup on DB failure
- change delete sequencing to commit DB delete before storage deletion
- preserve current response payloads

### `services/search_api/app/main.py`
- validate `top_k` as a positive integer
- keep existing request/response shapes

### `services/media_worker/app/main.py`
- preserve endpoint surface
- ensure processing failure behavior stays explicit and bounded

### `services/shared/semedia_shared/pipeline.py`
- handle missing media rows safely
- validate scene/caption/embedding count invariants
- replace destructive early scene deletion with safer replacement flow
- improve failure cleanup for derived files

### `services/shared/semedia_shared/search_service.py`
- change `scene_key` generation to stable ID-backed identity
- remove dependence on non-unique filenames for result identity

### `services/shared/semedia_shared/storage.py`
- add any helper behavior needed for rollback cleanup and deterministic orphan cleanup

### `services/shared/semedia_shared/index_service.py`
- keep current architecture
- add explicit rebuild/resync support for maintenance use

### `services/shared/semedia_shared` maintenance module(s)
- add recovery utilities for stuck media, storage consistency, and index repair

### Tests
- `testing/services/test_gateway_api.py`
- `testing/services/test_search_api.py`
- `testing/services/test_media_worker_api.py`
- `testing/services/test_media_worker_pipeline.py`
- any new focused service tests needed for maintenance/recovery behavior

## 9. Implementation Order

### Phase A — small boundary fixes
1. invalid upload media-type returns 422
2. positive `top_k` validation
3. missing-media safety in worker processing
4. stable `scene_key`

### Phase B — transactional hardening
1. upload cleanup on DB failure
2. rollback-safe delete sequencing
3. index rebuild error handling stays explicit and repairable

### Phase C — processing integrity
1. scene/caption/embedding count validation
2. safer scene replacement flow
3. derived-file cleanup for failed processing
4. clearer recoverability for stuck processing states

### Phase D — maintenance and repair
1. stuck media detection and repair actions
2. orphaned/missing file detection and cleanup
3. keyword-index rebuild/resync entrypoint

This ordering lands the lowest-risk correctness wins first and postpones the trickiest pipeline invariants until the simpler failures are already covered.

## 10. Testing Strategy

### 10.1 Boundary tests
Add or update tests to verify:
- invalid upload media type returns 422 instead of an unhandled failure
- non-integer `top_k` returns 422
- `top_k=0` returns 422
- negative `top_k` returns 422
- `scene_key` is stable and unique based on durable IDs

### 10.2 Failure-path tests
Add or update tests to verify:
- upload DB failure removes the just-written file
- delete DB failure does not delete files prematurely
- missing media processing is bounded and non-crashing
- mismatched scene/caption/embedding counts fail processing explicitly
- failed video reprocessing preserves the previous valid scene set or otherwise fails in the explicitly defined safe state
- post-failure derived-file cleanup behaves deterministically

### 10.3 Recovery tests
Add focused tests for:
- stuck `PENDING` / `PROCESSING` detection
- orphaned-file detection
- missing-file reference detection
- keyword-index rebuild/resync behavior

### 10.4 Verification commands
Use the repo’s standard Docker-based backend test flow after implementation. Prioritize the affected service tests first, then the full backend service suite.

Because this work targets backend correctness and reliability rather than search-quality tuning, `docs/metrics/search_quality_history.md` should only change if search result semantics materially change beyond validation or identity hardening.

## 11. Risks and Tradeoffs

### 11.1 Commit-first delete can leave temporary storage orphans
This is intentional. Temporary orphaned files are easier to recover from than DB rows pointing at already-deleted files.

### 11.2 Background dispatch remains non-durable at execution time
This design accepts that limitation because of the no-new-infrastructure constraint. The mitigation is explicit detection and recovery, not pretending the current dispatch is durable.

### 11.3 Safer scene replacement may require slightly more code complexity
That complexity is justified because the current behavior can destroy previously valid indexed scene state after a later processing failure.

### 11.4 Maintenance tooling introduces operator-facing behavior
This is acceptable because the user explicitly requested recovery support for already-bad state in existing environments.

## 12. Success Criteria

This design is complete when:
- invalid upload media types and invalid `top_k` values fail explicitly and consistently
- upload/delete flows no longer create the known DB/filesystem divergence paths
- missing media and processing failures are handled without unexpected crash behavior
- scene replacement preserves the last known-good indexed scene set unless the full new set is ready
- `scene_key` is globally unique and stable
- recovery utilities exist for stuck media, storage inconsistencies, and keyword-index resync
- affected backend service tests cover the new behavior

## 13. Recommendation

Proceed with implementation as a staged hardening pass inside the existing services.

This design addresses the highest-value backend correctness and reliability failures while staying within the stated constraints:
- no new infrastructure
- compatibility-first public API behavior
- recovery for already-bad state
- broad cleanup without architectural overreach
