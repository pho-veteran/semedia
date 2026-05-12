# Codebase Audit Report

Date: 2026-05-12

## 1. System Overview

### 1.1 Top-level structure mapped

The repository is organized around a Dockerized semantic media search system:

- `services/gateway_api/` — public FastAPI API for upload, media CRUD, runtime proxy, search proxy, and static media serving.
- `services/media_worker/` — internal FastAPI worker for media processing, captioning, scene extraction, and CLIP embeddings.
- `services/search_api/` — internal FastAPI search service for query embedding orchestration and retrieval.
- `services/shared/semedia_shared/` — shared data model, database/session setup, processing pipeline, storage, ML helpers, keyword index, search, ranking, serialization, and runtime helpers.
- `frontend/` — React + TypeScript + Vite UI consuming the gateway API.
- `testing/` — pytest service tests, evaluation benchmark code/artifacts, and smoke tests.
- `docs/` — plans, implementation notes, benchmark/tuning records, and project documentation.

The runtime topology is defined in `docker-compose.yml`: PostgreSQL, `media-worker`, `search-api`, `gateway-api`, `frontend`, and a `service-tests` profile image. Only `gateway-api` and `frontend` are host-exposed; `search-api` and `media-worker` are internal services.

### 1.2 Service architecture and end-to-end data flow

#### Upload and processing flow

1. Frontend uploads a file through `uploadMediaFile()` in `frontend/src/api/client.ts:57-65` to `POST /api/v1/media/upload/`.
2. Gateway validates/infer media type, saves the upload, creates a `MediaItem`, and enqueues a FastAPI background task to call the media worker (`services/gateway_api/app/main.py:126-168`).
3. Gateway dispatch is an HTTP background task, not a durable queue (`services/gateway_api/app/main.py:75-92,157`).
4. Media worker receives `POST /internal/media/{media_id}/process` and calls `process_media()`.
5. `process_media()` loads the row, marks it processing, branches image/video, commits completed status, then rebuilds the keyword index (`services/shared/semedia_shared/pipeline.py:18-58`).
6. Images are captioned and embedded once (`pipeline.py:61-69`).
7. Videos are segmented into scenes, one midpoint keyframe/thumbnail is written per scene, each keyframe is captioned and embedded, previous scenes are replaced, and a short media-level caption is derived from up to three unique scene captions (`pipeline.py:72-135`, `video_service.py:47-97`).

#### Text search flow

1. Frontend calls `searchMedia()` with `{ query_text, top_k }` (`frontend/src/api/client.ts:73-84`).
2. Gateway proxies the JSON body to `search-api` (`services/gateway_api/app/main.py:225-237`).
3. Search API strips and validates `query_text`, coerces `top_k` to a positive integer, and synchronously asks `media-worker` for a text CLIP embedding (`services/search_api/app/main.py:54-63,81-94,129-139`).
4. `search_text()` runs vector search, keyword search, candidate merge, weighted fusion, heuristic reranking, diversity filtering, score clamping, and result serialization (`services/shared/semedia_shared/search_service.py:139-149`; `ranking_service.py:29-145`).
5. Frontend applies client-side filtering/sorting/grouping to the already-returned result slice (`frontend/src/pages/SearchPage.tsx:91-115,214-275,543-597`; `frontend/src/utils/searchResults.ts:6-57`).

#### Image search flow

1. Frontend uploads a query image via `searchMediaByImage()` (`frontend/src/api/client.ts:86-95`).
2. Gateway proxies multipart file data to `search-api` (`services/gateway_api/app/main.py:240-264`).
3. Search API validates the uploaded query file is an image and synchronously asks `media-worker` for an image CLIP embedding (`services/search_api/app/main.py:142-165`).
4. `search_image()` runs vector-only retrieval through the same ranking/diversity/scoring path (`services/shared/semedia_shared/search_service.py:152-161`).

### 1.3 Data model summary

- `MediaItem` stores uploaded media metadata, status, caption, embedding, and `index_key` (`services/shared/semedia_shared/models.py:28-54`).
- `VideoScene` stores per-scene `scene_index`, timestamps, keyframe/thumbnail paths, caption, embedding, and `index_key`; `(media_id, scene_index)` is unique (`models.py:65-86`).
- `KeywordIndexArtifact` stores one compressed pickled TF-IDF artifact keyed as `default` (`models.py:89-98`; `index_service.py:111-158`).

### 1.4 Traced file and function inventory

This audit traced the following files and functions/code paths:

#### Backend services and shared infrastructure

- `services/gateway_api/app/main.py`
  - lifespan/database/static media/CORS setup: `33-53`
  - worker dispatch: `_trigger_worker_processing()` `75-92`
  - upload: `upload_media()` `126-168`
  - list/detail/delete: `list_media()`, `get_media_detail()`, `delete_media()` `171-222`
  - search proxy: `search()` and `search_by_image()` `225-264`
- `services/search_api/app/main.py`
  - startup keyword-index load: `23-35`
  - `top_k` validation: `_coerce_positive_top_k()` `54-63`
  - embedding calls: `_embed_text()`, `_embed_image()` `81-121`
  - text/image search endpoints: `129-165`
- `services/media_worker/app/main.py`
  - traced by subsystem auditors for embedding and processing endpoints: `64-121`
- `services/shared/semedia_shared/models.py`
  - `MediaItem`, `VideoScene`, `KeywordIndexArtifact` `28-98`
- `services/shared/semedia_shared/pipeline.py`
  - `process_media()`, `_process_image()`, `_process_video()`, scene-output validation, caption summary helpers `18-166`
- `services/shared/semedia_shared/video_service.py`
  - `SceneSpan`, `get_video_duration()`, adaptive thresholding, `detect_scenes()`, `extract_scene_keyframe()` `6-97`
- `services/shared/semedia_shared/caption_service.py`
  - caption cleanup, weak detection, batch generation, retry flow, fallback, warmup `13-276`
- `services/shared/semedia_shared/caption_cleanup_config.py`
  - cleanup rule sets traced by subagent: `5-77`
- `services/shared/semedia_shared/clip_service.py`
  - `_normalize()`, CLIP loading, image/text encoding, deterministic fallback handling, warmup `13-151`
- `services/shared/semedia_shared/index_service.py`
  - keyword index build/serialize/persist/load/rebuild/search/cache-refresh `25-270`
- `services/shared/semedia_shared/search_service.py`
  - cosine search, result serialization, scene key generation, text/image search `15-161`
- `services/shared/semedia_shared/ranking_service.py`
  - candidate merge, reranking, diversity, calibration, explanation, ranking `7-145`
- `services/shared/semedia_shared/serialization.py`
  - media summary/detail and scene detail serialization traced by subagent: `6-43`
- `services/shared/semedia_shared/storage.py`
  - storage and URL helpers traced by subagent: `10-71`
- `services/shared/semedia_shared/config.py`
  - ML/search/caption settings traced by subagent: `7-83`
- `services/shared/semedia_shared/runtime.py`, `model_warmup.py`, `hf_loader.py`, `ml_inputs.py`, `media_types.py`, `database.py`, `log.py`
  - traced by subagents for service startup, ML runtime, media validation, and database bootstrap.

#### Frontend

- `frontend/src/api/client.ts`
  - upload, search, image search, media API calls `57-95`
- `frontend/src/types/api.ts`
  - API models, notably `SearchResult` missing backend `scene_key`/`scene_index` fields `52-90`
- `frontend/src/utils/searchResults.ts`
  - scene grouping by `media_id` `6-57`
- `frontend/src/pages/SearchPage.tsx`
  - client-side filters/sorts/search submission/rendering traced by subagents `91-115,214-275,543-597`
- `frontend/src/components/SearchResultCard.tsx`
  - result display and explanation badges traced by subagents `12-169`
- `frontend/src/components/SearchResultGroup.tsx`
  - grouped-scene rendering traced by subagents `17-165`
- `frontend/src/pages/MediaDetailPage.tsx`
  - scene display/deep-link behavior traced by subagents `34-431`
- `frontend/src/App.tsx`, `frontend/src/pages/DashboardPage.tsx`, `frontend/src/pages/LibraryPage.tsx`, `frontend/src/utils/format.ts`, `frontend/src/config.ts`, `frontend/src/main.tsx`
  - traced by architecture subagent for app routing, polling, display, and URL/format helpers.

#### Evaluation and benchmark artifacts

- `testing/evaluation/evaluate_search.py`
  - query loading, metric computation, grouped summaries, negative-query summary, report comparison, result identifier normalization, evaluation loop `14-217`
- `testing/evaluation/run_evaluation.py`
  - CLI validation/load/run/compare/write path `24-169`
- `testing/evaluation/benchmark_validation.py`
  - strict schema validation, scene-key validation, asset-manifest validation, audit-log validation, sign-off helpers `35-228`
- `testing/evaluation/seed_media.py`
  - upload/poll/manifest seeding path traced by subagent `15-101`
- `testing/evaluation/queries.json`
  - 120-query locked benchmark with integer media IDs and filename-based scene keys, traced by subagent.
- `testing/evaluation/asset_manifest.json`
  - locked corpus manifest traced by subagent.
- `testing/evaluation/audit_log.json`
  - currently empty, traced by subagent.
- `testing/evaluation/baselines/baseline-phase7.json`
  - saved baseline sampled by subagent, including numeric scene IDs in retrieved results.
- `testing/evaluation/test_evaluate_search.py`, `test_full_evaluation.py`, `test_benchmark_validation.py`, `test_manifest_lock.py`
  - metric, schema, baseline, and rigor tests traced by subagent.

#### Documentation checked for alignment

- `CLAUDE.md`
- `docs/plan.md`
- `docs/TASKS.md`
- `docs/metrics/search_quality_history.md`
- `docs/metrics/search_tuning_checklist.md`
- `docs/metrics/evaluation_benchmark_rubric.md`
- `docs/implementations/phase6-ranking-explanations.md`

## 2. Component Breakdown

### 2.1 Gateway API

The gateway is a public-facing FastAPI proxy/orchestrator. It owns upload persistence, media listing/detail/deletion, static file serving, runtime proxying, and forwarding search calls to `search-api`.

Key observations:

- Upload uses FastAPI `BackgroundTasks` to call the worker over HTTP (`services/gateway_api/app/main.py:126-168`).
- Dispatch failures are caught and can mark media failed (`gateway_api/app/main.py:75-92`), but there is no durable queue/outbox, retry schedule, or worker claim model.
- Delete removes the row, deletes files, and then synchronously rebuilds the keyword index (`gateway_api/app/main.py:202-222`).
- List/detail eagerly load scenes with `selectinload()` even when only summaries are needed (`gateway_api/app/main.py:177-188,192-199`).
- Search endpoints do no retrieval locally; they proxy to `search-api` (`gateway_api/app/main.py:225-264`).

### 2.2 Media worker and processing pipeline

The media worker owns ML-heavy processing and query embeddings.

Image path:

- `generate_captions(settings, [path])`
- `encode_images(settings, [path])`
- store `media.caption`, `media.embedding`, `media.index_key = media:{id}` (`pipeline.py:61-69`).

Video path:

- duration via OpenCV (`video_service.py:13-24`)
- adaptive threshold scene detection (`video_service.py:27-72`)
- midpoint keyframe extraction and duplicate thumbnail write (`video_service.py:75-97`)
- batch captioning of keyframes (`pipeline.py:97-105`)
- embedding of keyframes (`pipeline.py:105`)
- replace `VideoScene` rows, each with `index_key = scene:{media_id}:{scene_index}` (`pipeline.py:108-131`)
- derive video `media.caption` from first three unique scene captions, truncated to 200 chars (`pipeline.py:128,151-166`).

### 2.3 Search API and retrieval core

Search API validates input, obtains query embeddings synchronously from media worker, then calls shared search functions.

Retrieval components:

- Vector candidates: brute-force Python/NumPy cosine scan over all completed images and all video scenes (`search_service.py:78-129`).
- Keyword candidates: cached durable TF-IDF artifact over captions only (`index_service.py:47-108,193-204,207-270`).
- Fusion/ranking: candidate merge by DB identity, fixed weighted fusion, simple caption heuristics, per-media cap, global caption dedupe for text mode, score clamp (`ranking_service.py:29-145`).
- Serialization: result payload includes `scene_id`, `scene_index`, `scene_key`, score components, caption, URLs, timestamps, and explanation (`search_service.py:55-75`).

### 2.4 Frontend search UX

The frontend receives raw result rows, then:

- filters by media type and minimum score client-side;
- sorts by relevance/date/size client-side;
- groups multiple video scene rows from the same `media_id` into one grouped render entry (`frontend/src/utils/searchResults.ts:6-57`);
- displays DB `scene_id` in scene badges even though backend returns `scene_index` (`frontend/src/types/api.ts:59-76` omits `scene_index` and `scene_key`).

This means UI sorting/filtering operates only over the already-truncated backend result slice, not the full corpus.

### 2.5 Evaluation stack

Evaluation has three layers:

- Artifact validation: strict benchmark schema, scene-key format, manifest coverage, audit-log shape (`benchmark_validation.py:35-228`).
- Metric library: load queries, call a search function per query, normalize IDs, compute precision/recall/MRR/NDCG, summarize by type/modality/difficulty/negative queries (`evaluate_search.py:14-217`).
- Live CLI: validate artifacts, call live gateway text search API, run metrics, compare baseline, optionally write output (`run_evaluation.py:24-169`).

The evaluation path is text-query shaped only: `run_evaluation()` accepts `Callable[[str, int], list[dict]]` and passes `query["query_text"]` (`evaluate_search.py:126-167`).

## 3. Algorithm Deep-Dive

### 3.1 Vector retrieval

Implementation:

- `_completed_media()` loads every completed `MediaItem` and all scenes with `selectinload()` (`search_service.py:29-36`).
- `_vector_results()` converts the query embedding to NumPy, computes cosine against each image embedding and each scene embedding, appends dict candidates, sorts all candidates descending, and returns `top_k` (`search_service.py:78-129`).

Complexity:

- Let `M` be completed images, `S` completed scenes, `N=M+S`, and `d` embedding dimension.
- Time: `O(N*d + N log N)` per query.
- Space: `O(N)` candidate dicts plus ORM-loaded media/scene objects.

Implicit assumptions:

- Entire corpus can be hydrated into Python memory on every query.
- Exact brute-force scan is acceptable.
- Stored embeddings and query embeddings share the same model/dimension.
- Negative cosine values can be clamped to zero without losing useful ordering.

### 3.2 Keyword retrieval

Implementation:

- `build_keyword_index()` scans completed images/scenes, indexes image captions and scene captions, and fits `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)` (`index_service.py:47-108`).
- The artifact is pickled, gzipped, and stored in `KeywordIndexArtifact.payload` (`index_service.py:111-158`).
- `search_keyword()` transforms the query, computes cosine similarity against the full matrix, filters positive scores, sorts all positives, and returns `top_k` (`index_service.py:193-204`).
- `ensure_keyword_index_current()` caches by artifact metadata including `payload` bytes (`index_service.py:207-270`).

Complexity:

- Build: roughly `O(total_caption_tokens)` plus sparse matrix construction; memory `O(nnz(tfidf_matrix) + payload_count)`.
- Query: `O(nnz(query) + matrix_similarity + R log R)`, where `R` is positive-scored documents.
- Rebuild: full corpus refit on every successful ingest and delete (`pipeline.py:49-55`; `gateway_api/app/main.py:217-222`).

Implicit assumptions:

- Captions are the only useful lexical field; filenames, OCR, ASR, tags, and metadata are ignored.
- Full-library TF-IDF rebuild is cheap enough.
- One compressed DB blob is acceptable for index persistence and cache invalidation.

### 3.3 Hybrid fusion and ranking

Implementation:

- `search_text()` asks vector and keyword branches for only `limit` candidates each (`search_service.py:139-142`).
- `merge_candidates()` merges by tuple key: `("image", media.id)` or `("scene", scene.id)` (`ranking_service.py:29-45`; candidate keys built in `search_service.py:87-113` and `index_service.py:56-81`).
- Text fusion uses fixed weights: `vector * settings.search_vector_weight + keyword * settings.search_keyword_weight` (`ranking_service.py:125-135`).
- Reranking adds `0.08` if normalized query is a substring of normalized caption, and `0.02` if caption length exceeds 50 (`ranking_service.py:47-63`).
- Diversity caps per media and globally dedupes identical normalized captions in text mode (`ranking_service.py:66-88,138-142`).
- Final score calibration is only clamp/round, not statistical calibration (`ranking_service.py:91-94`; `search_service.py:23-26,39-40`).

Complexity:

- Merge: `O(V+K)`.
- Reranking: roughly `O(C * caption_length)`.
- Sorting: `O(C log C)`.
- Diversity: `O(C)`.

Implicit assumptions:

- CLIP cosine and TF-IDF cosine are comparable after simple clamping.
- Fixed weights work across query types.
- Caption length is a useful proxy for informativeness.
- Exact substring match is a reliable relevance boost.
- Global caption dedupe improves results more than it harms recall.

### 3.4 Result identity and scene-key handling

Persisted identities:

- `MediaItem.id` and `MediaItem.index_key = media:{id}` (`models.py:31-41`; `pipeline.py:67,129`).
- `VideoScene.id`, `(media_id, scene_index)`, and `VideoScene.index_key = scene:{media_id}:{scene_index}` (`models.py:68-85`; `pipeline.py:120`).

Search identities:

- Merge keys use DB row identity: `("scene", scene.id)` (`search_service.py:110-113`; `index_service.py:78-81`).
- API scene key uses filename and scene index where possible: `scene:{original_filename}:{scene_index}` (`search_service.py:43-48`).
- Fallback scene key has a bug: `return f"scene:{scene_id}",` returns a tuple, not a string (`search_service.py:49-52`).

Evaluation identities:

- Relevant media IDs normalize to `media:{id}` (`benchmark_validation.py:44-54`; `evaluate_search.py:157-163`).
- Relevant scene IDs must be `scene:<video filename>:<scene_index>` in strict validation (`benchmark_validation.py:35-41,124-128`).
- Result identifiers prefer `scene_key`, then numeric `scene_id`, then `media_id` (`evaluate_search.py:117-123`).

Implicit assumptions:

- `original_filename` is unique enough to identify a video in benchmark/search contexts.
- Search responses always include a string `scene_key` when evaluation needs stable scene matching.
- DB ids are stable enough for media ground truth.

### 3.5 Caption generation and cleanup

Implementation:

- `_normalize_caption_signal()` lowercases, strips punctuation, removes malformed tokens, applies substring rewrite rules, and collapses double spaces (`caption_service.py:29-37`).
- `_clean_caption()` capitalizes the normalized caption and appends punctuation (`caption_service.py:40-51`).
- `_is_weak_caption()` flags short, generic, or low-word-count captions (`caption_service.py:54-66`).
- `generate_captions()` loads resources, batches image paths, runs base generation, queues weak captions for retry, reruns them with stricter settings, and falls back if still weak (`caption_service.py:168-241`).
- If caption model loading/inference fails and strict CUDA is not active with selected device `cuda`, deterministic fallback captions are returned (`caption_service.py:181-184,237-241`).

Complexity:

- Let `N` be images/keyframes and `B` batch size.
- Time: dominated by model inference, roughly `O(ceil(N/B))` batches plus optional retry batches.
- Space: materializes all paths, opens one batch of images at a time, stores captions and retry queues.

Downstream retrieval effect:

- Image captions and scene captions are the entire keyword corpus (`index_service.py:51-93`).
- Captions drive exact-phrase/rich-caption rerank boosts (`ranking_service.py:47-63`).
- Captions drive global text-mode dedupe (`ranking_service.py:76-81`).
- Weak fallback text can become searchable content unless excluded elsewhere; currently it is not excluded (`caption_service.py:232-234`; `index_service.py:52-76`).

### 3.6 Scene detection and keyframe extraction

Implementation:

- Duration is computed via OpenCV frame count / FPS (`video_service.py:13-24`).
- Threshold is `20.0` for videos under 30s, `35.0` for videos over 10 minutes, otherwise `settings.scene_detection_threshold` (`video_service.py:27-44`).
- PySceneDetect `ContentDetector` produces spans; if none are found but duration is positive, the entire video becomes one scene (`video_service.py:47-72`).
- Keyframe is the midpoint frame; the same frame is written to both keyframe and thumbnail paths (`video_service.py:75-97`).

Complexity:

- Scene detection: roughly `O(video_frames)`.
- Keyframe extraction: one seek/read per scene.
- Captioning/embedding after extraction: `O(num_scenes)` model work.

Implicit assumptions:

- The midpoint frame represents the whole scene.
- Static thresholds generalize to varied videos.
- Thumbnail can be identical to full keyframe without storage/bandwidth consequences.

### 3.7 Evaluation metrics

Implementation:

- `compute_metrics()` slices `top_k`, counts membership hits, computes precision@k, recall@k, MRR over the full retrieved list, and binary NDCG@k (`evaluate_search.py:18-45`).
- `run_evaluation()` filters judged queries, normalizes relevant IDs, calls `search_fn(query_text, k)`, maps result IDs, computes metrics, and averages them (`evaluate_search.py:126-217`).
- Negative queries count any returned IDs as false positives (`evaluate_search.py:66-78`).
- Baseline comparison flags relative drops in aggregate metrics and a fixed `+0.05` increase in negative-query false-positive rate (`evaluate_search.py:81-114`).

Complexity:

- Per query metric work: `O(len(retrieved_ids) + k + len(relevant_ids))`.
- Full evaluation local work: `O(Q * (retrieved + k + relevant))`, dominated in practice by `Q` live API calls.
- With per-query reporting, space is `O(Q*k)` for retrieved IDs.

Implicit assumptions:

- Retrieved IDs are unique.
- Binary relevance is sufficient.
- Text queries cover the relevant retrieval behavior.
- Returning any item for a negative query is a false positive, regardless of score/confidence.

## 4. Identified Weaknesses

### 4.1 Retrieval and ranking weaknesses

#### W1 — Vector search is full-corpus Python scan

Evidence: `_completed_media()` loads all completed media and scenes (`services/shared/semedia_shared/search_service.py:29-36`), and `_vector_results()` computes cosine for every image and every scene, sorts all results, then slices (`search_service.py:78-129`).

Impact: Query latency and memory grow linearly with corpus size and scene count, with additional `O(N log N)` sorting. This is the main scalability ceiling.

#### W2 — Hybrid candidate generation truncates before fusion

Evidence: vector results return only `top_k` (`search_service.py:128-129`), keyword results return only `top_k` (`index_service.py:203-204`), and fusion happens after both truncations (`search_service.py:139-145`).

Impact: A candidate that is moderately strong in both modalities but not top-k in either individual branch can never be fused into the final result. This is a correctness/recall issue, not just a performance choice.

#### W3 — Score “normalization” is only clamping

Evidence: `_normalize_scores()` clamps scores to `[0, 1]` (`search_service.py:23-26`), and `_clamp_score()` is used before fixed weighted fusion (`ranking_service.py:13-14,128-135`).

Impact: CLIP cosine and TF-IDF cosine are treated as commensurate distributions. Negative vector scores are collapsed to `0`, and fixed weights may over/underweight a signal depending on query and corpus distribution.

#### W4 — `top_k` is unbounded

Evidence: `_coerce_positive_top_k()` only checks integer and `> 0` (`services/search_api/app/main.py:54-63`).

Impact: Large `top_k` values can amplify CPU, memory, sorting, and response costs. This is both an accidental performance footgun and a public API abuse vector.

#### W5 — Global caption dedupe can hide distinct relevant items

Evidence: `_apply_diversity()` dedupes exact normalized captions across the entire text result set (`ranking_service.py:66-88`).

Impact: Different assets with identical/generated/generic captions can suppress each other even when they are independently relevant. This particularly hurts scenes or fallback captions with repeated text.

#### W6 — Reranking heuristics are brittle

Evidence: exact phrase boost is substring matching (`ranking_service.py:55-56`), and rich-caption boost is only caption length greater than 50 (`ranking_service.py:58-59`).

Impact: Substrings can over-fire, length can reward verbosity rather than relevance, and fixed boost constants are not query-aware.

#### W7 — Image-query fallback can become random relative to content

Evidence: `encode_images()` falls back to `embedding_from_path(path)` if CLIP image inference fails outside strict CUDA (`clip_service.py:78-82`). Query images are proxied through uploaded file streams and worker temp handling, so fallback semantics can depend on path/name rather than pixels. Text fallback uses `embedding_from_text()` (`clip_service.py:108-112`).

Impact: Silent fallback preserves uptime but can make retrieval nonsensical and benchmark-invalid when fallback activates.

#### W8 — Video-level retrieval is missing

Evidence: videos get an aggregate `media.caption` (`pipeline.py:128-130`), but vector and keyword retrieval only use image-level media rows and scene rows (`search_service.py:82-127`; `index_service.py:51-93`).

Impact: Queries about an entire video concept may be missed if no single scene caption/embedding captures it well.

### 4.2 Scene-key and identifier weaknesses

#### W9 — `_stable_scene_key()` returns a tuple in fallback path

Evidence: `return f"scene:{scene_id}",` has a trailing comma (`services/shared/semedia_shared/search_service.py:49-52`).

Impact: If filename/scene index are unavailable, API emits a tuple-like value instead of a string, and evaluation `_result_identifier()` will treat it as truthy (`testing/evaluation/evaluate_search.py:117-123`).

#### W10 — Filename-based scene keys are not globally unique

Evidence: preferred external scene key is `scene:{original_filename}:{scene_index}` (`search_service.py:43-48`), while `MediaItem.original_filename` is not unique (`models.py:31-34`).

Impact: Two uploaded videos with the same original filename and scene index collide externally, affecting evaluation, caching, frontend identity, and any downstream analytics.

#### W11 — Internal and external scene identities disagree

Evidence: merge keys use DB `scene.id` (`search_service.py:110-113`; `index_service.py:78-81`), persistent index keys use `scene:{media_id}:{scene_index}` (`pipeline.py:120`), search API scene keys use filename/scene index (`search_service.py:43-48`), detail API exposes `index_key` but not `scene_key` (`serialization.py` traced by subagent), and frontend types omit `scene_key`/`scene_index` (`frontend/src/types/api.ts:59-76`).

Impact: Reprocessing/deleting/recreating scenes can change DB IDs while preserving semantic scene identity. Search, detail, evaluation, and UI cannot consistently refer to the same scene through one canonical field.

#### W12 — Frontend displays DB scene IDs instead of scene order

Evidence: backend returns `scene_index` and `scene_key` (`search_service.py:55-75`), but `SearchResult` type omits both (`frontend/src/types/api.ts:59-76`). UI components traced by subagents use `scene_id` in scene badges.

Impact: Users see unstable database identifiers instead of human-meaningful scene numbers, and React keys/grouping cannot use canonical scene identity.

### 4.3 Caption-generation and retrieval-quality weaknesses

#### W13 — Caption cleanup uses broad substring replacement

Evidence: `_normalize_caption_signal()` applies `.replace()` for malformed tokens and rewrite rules (`caption_service.py:29-37`).

Impact: Non-boundary-aware cleanup can remove valid substrings or miss variants. Because captions feed keyword search, reranking, dedupe, and UI, cleanup mistakes propagate widely.

#### W14 — Weak/fallback captions become searchable content

Evidence: weak retry fallback assigns `settings.caption_retry_fallback` (`caption_service.py:231-234`), and keyword index includes every non-empty image/scene caption (`index_service.py:52-76`).

Impact: Low-signal fallback text can produce junk keyword hits, distort TF-IDF, and interact badly with global caption dedupe.

#### W15 — Adjacent duplicate scene captions are mutated with display text

Evidence: identical adjacent captions are changed to `"... (scene N)"` (`pipeline.py:100-103`).

Impact: Display disambiguation pollutes retrieval text with non-semantic tokens. It only handles adjacent duplicates and leaves non-adjacent duplicates untouched.

#### W16 — Video summary is first-scene-biased

Evidence: video `media.caption` is first three unique scene captions joined and truncated to 200 chars (`pipeline.py:128,151-166`).

Impact: Later salient scenes are omitted. Current retrieval mostly uses scene captions, but summaries shown in UI or future parent-video retrieval inherit this bias.

#### W17 — One midpoint keyframe per scene is a weak representation

Evidence: `extract_scene_keyframe()` chooses midpoint time and extracts one frame (`video_service.py:75-97`).

Impact: Long/action-heavy scenes may be represented by an uninformative still, weakening both caption quality and CLIP embedding quality.

#### W18 — Thumbnail generation duplicates keyframes

Evidence: the same frame is written to both `keyframes/` and `thumbnails/` without resize/compression difference (`video_service.py:88-97`).

Impact: Doubles IO/storage for scene imagery without actual thumbnail benefit.

### 4.4 Architecture and operations weaknesses

#### W19 — No durable processing queue

Evidence: upload dispatch uses FastAPI `BackgroundTasks` and direct HTTP call to worker (`gateway_api/app/main.py:75-92,126-168`).

Impact: Gateway crash/restart after response can strand work; retries and observability are limited.

#### W20 — Search availability depends on media worker availability

Evidence: search-api synchronously calls media-worker for every text and image embedding (`services/search_api/app/main.py:81-121`).

Impact: Search latency/availability inherits ML worker model loading, GPU state, and network failures.

#### W21 — Full keyword index rebuild is synchronous after mutations

Evidence: successful processing rebuilds keyword index (`pipeline.py:49-55`), and delete does the same (`gateway_api/app/main.py:217-222`).

Impact: Ingest/delete latency grows with corpus size and can cause lock/contention issues.

#### W22 — List/detail eager-load scenes broadly

Evidence: list and detail use `selectinload(MediaItem.scenes)` (`gateway_api/app/main.py:177-188,192-199`), while summaries only need scene count.

Impact: Video-heavy libraries pay unnecessary DB and serialization overhead.

#### W23 — Public API has MVP security posture

Evidence: permissive CORS can be enabled with `allow_origins=["*"]` (`gateway_api/app/main.py:46-53`; `search_api/app/main.py:40-47`), and public gateway exposes upload/list/detail/delete/search without auth/rate limits.

Impact: Acceptable for local MVP, risky for shared or internet-exposed deployments.

### 4.5 Evaluation and benchmark-rigor issues

#### BR1 — Scene evaluation depends on stable `scene_key`, but baseline evidence shows numeric scene IDs

Evidence: evaluation result IDs prefer `scene_key` then numeric `scene_id` (`evaluate_search.py:117-123`); strict scene truth expects `scene:<filename>:<scene_index>` (`benchmark_validation.py:35-41`). The Phase 7 baseline sampled by subagents contains numeric retrieved IDs such as `scene:2`, `scene:3`, etc.

Impact: If live results lack canonical `scene_key`, canonical scene ground truth cannot match numeric scene IDs. This likely explains all-zero video/action slices reported in benchmark history.

#### BR2 — Media ground truth depends on DB insertion order

Evidence: `relevant_media_ids` validate as positive integers (`benchmark_validation.py:124-125`), and evaluation normalizes them as `media:{id}` (`benchmark_validation.py:47-54`; `evaluate_search.py:157-163`). Seeder uploads manifest files sequentially and prints returned IDs but does not persist or validate an asset-to-media mapping (traced in `testing/evaluation/seed_media.py:15-101`).

Impact: Seeding into a non-empty DB, partial reseeding, or manifest order changes can invalidate the benchmark silently.

#### BR3 — Strict validation is optional in the metric library

Evidence: `load_benchmark_definition(..., strict=False)` accepts top-level lists and injects default judgment policy (`benchmark_validation.py:68-82`), and `evaluate_search.load_queries()` calls it without strict mode (`evaluate_search.py:14-15`).

Impact: CLI validates strictly, but library consumers and many tests can run ad hoc non-locked schemas, weakening the locked-benchmark guarantee.

#### BR4 — Duplicate retrieved IDs can inflate metrics

Evidence: `compute_metrics()` counts every occurrence in `top_k`, with no dedupe (`evaluate_search.py:18-45`).

Impact: Duplicate relevant IDs can inflate precision/DCG and even make recall exceed 1.0 if duplicates repeat a single relevant item.

#### BR5 — Negative-query metric is saturated and confidence-blind

Evidence: negative summary treats any retrieved ID as a false positive and counts raw result length (`evaluate_search.py:66-78`).

Impact: If search normally returns `top_k` low-confidence tail results, false-positive rate will saturate at 1.0 and stop being diagnostic.

#### BR6 — Sign-off helpers are not enforced by the runner

Evidence: validation exposes `audit_log_has_blockers()` and `can_sign_off_benchmark()` (`benchmark_validation.py:217-222`), but `run_evaluation.py` only calls `validate_benchmark_artifacts()` (`run_evaluation.py:94-98`).

Impact: Documented benchmark sign-off can be bypassed in actual evaluation runs.

#### BR7 — Evaluation is text-query only

Evidence: `run_evaluation()` takes `Callable[[str, int], list[dict]]` and passes `query["query_text"]` (`evaluate_search.py:126-167`); CLI calls only `/api/v1/search/` (`run_evaluation.py:24-35,115-128`).

Impact: Image-query retrieval quality is not covered by the locked evaluation path.

#### BR8 — Accepted baseline appears to preserve known-bad slices

Evidence: subagent review of `docs/metrics/search_quality_history.md` and `baseline-phase7.json` found accepted baseline slices with all-zero video/action/hard metrics and negative false-positive rate 1.0.

Impact: Baseline may be useful as a frozen reference, but it is weak as a quality gate unless known-bad slices are explicitly tracked as blockers.

## 5. Improvement Recommendations (ranked by impact)

### 1. Canonicalize scene identity across backend, frontend, and evaluation

Change:

- Introduce one external scene identifier that is stable and unique, preferably filename-independent.
- Use it in `VideoScene`, search payloads, detail payloads, evaluation truth, frontend React keys, and logs.
- Stop mixing DB row ID, `index_key`, filename `scene_key`, and `media_id + start_time` identity schemes.

Expected impact: Very high. This directly addresses evaluation correctness, reprocessing stability, duplicate filename collisions, and frontend consistency.

Tradeoff: Requires API/schema/test/baseline migration and compatibility handling for existing benchmark artifacts.

### 2. Fix `_stable_scene_key()` tuple bug immediately

Change:

- Remove the trailing comma from `return f"scene:{scene_id}",` in `services/shared/semedia_shared/search_service.py:52`.

Expected impact: High correctness benefit for a tiny patch.

Tradeoff: None.

### 3. Expand retrieval candidate breadth before fusion

Change:

- Add separate candidate-breadth settings, e.g. `SEARCH_VECTOR_CANDIDATE_K` and `SEARCH_KEYWORD_CANDIDATE_K`, larger than final `top_k`.
- Retrieve broad pools, then fuse/rerank/diversify down to final limit.

Expected impact: High relevance impact with less complexity than replacing the vector backend.

Tradeoff: More per-query CPU/memory until ANN/vector indexing exists.

### 4. Replace brute-force vector scan with a scalable vector index

Change:

- Near term: cache dense embedding arrays and use `heapq.nlargest` or partial top-k selection instead of ORM hydration + full sort.
- Medium term: use pgvector, FAISS, HNSW, or another ANN index keyed by canonical item IDs.

Expected impact: Highest scalability impact.

Tradeoff: More index lifecycle complexity and eventual consistency considerations.

### 5. Use calibrated fusion instead of clamp-only weighted sums

Change:

- Consider reciprocal rank fusion, per-modality z/quantile normalization, or benchmark-tuned calibration.
- Keep explanation fields but distinguish raw scores from calibrated/rank-based scores.

Expected impact: High ranking-quality impact, especially across mixed query types.

Tradeoff: Requires tuning/evaluation and may make scores less intuitively tied to raw cosine.

### 6. Make ML fallback explicit or fail closed for retrieval

Change:

- For production/evaluation, fail embedding/captioning when CLIP/caption model is unavailable instead of silently using deterministic fallback.
- If fallback remains for development, mark degraded mode in runtime/search metadata and avoid benchmark runs under fallback.
- For image fallback, hash image bytes rather than temp path if content-preserving fallback is desired.

Expected impact: High correctness and benchmark-validity impact.

Tradeoff: Reduced uptime when ML dependencies fail, but failures become observable.

### 7. Treat weak/fallback captions as quality metadata, not normal search text

Change:

- Add caption quality status (`usable`, `weak`, `fallback`) at media/scene level.
- Exclude fallback captions from keyword indexing, exact-phrase boosts, rich-caption boosts, and global caption dedupe.

Expected impact: High precision/noise improvement.

Tradeoff: Assets with failed captions may become less searchable lexically until recaptioned.

### 8. Move display disambiguation out of caption text

Change:

- Remove `"(scene N)"` mutation from retrieval captions.
- Render duplicate-scene labels in UI using `scene_index`/canonical scene ID.

Expected impact: Medium; improves corpus purity and avoids non-semantic TF-IDF tokens.

Tradeoff: Small frontend/API display adjustment.

### 9. Enforce strict benchmark validation and sign-off in all evaluation entry points

Change:

- Make `evaluate_search.load_queries()` strict by default for locked benchmark files.
- Make CLI fail if audit log has blockers or required sign-off criteria are unmet.
- Update tests that rely on reduced query schemas to use explicit helper fixtures or a non-locked mode.

Expected impact: High benchmark rigor impact.

Tradeoff: More ceremony for local metric experiments.

### 10. Migrate benchmark ground truth away from DB insertion IDs and filenames

Change:

- Use manifest asset IDs or immutable media/scene external IDs.
- Persist seed mapping and assert benchmark DB state before evaluation.

Expected impact: High benchmark correctness impact.

Tradeoff: Requires rewriting `queries.json`, seed scripts, validators, and baselines.

### 11. Deduplicate or assert unique retrieved IDs before metric computation

Change:

- Either score unique IDs only or fail if duplicate IDs appear in a result set.

Expected impact: Medium; prevents inflated metrics and surfaces upstream duplication.

Tradeoff: Historical scores may shift.

### 12. Redefine negative-query metrics around confidence thresholds

Change:

- Count false positives only above a calibrated score threshold, or add precision-at-threshold/abstention metrics.

Expected impact: Medium; makes negative-query reporting diagnostic instead of saturated.

Tradeoff: Requires a stable score threshold contract.

### 13. Add a hard `top_k` cap

Change:

- Clamp or reject `top_k` above `settings.search_max_results` or a new maximum.

Expected impact: Medium operational hardening.

Tradeoff: Less flexibility for large-result clients; pagination/candidate endpoints may be needed later.

### 14. Add video-level candidates

Change:

- Index aggregated video captions and/or pooled scene embeddings as parent-video candidates in addition to scene candidates.

Expected impact: Medium relevance improvement for whole-video queries.

Tradeoff: More candidate types, dedupe decisions, and evaluation expectations.

### 15. Improve scene representation

Change:

- Sample multiple frames per scene or choose representative frames by sharpness/visual variance.
- Generate real resized/compressed thumbnails.

Expected impact: Medium caption/embedding quality and storage efficiency gains.

Tradeoff: More ingest compute and storage/index complexity.

### 16. Move search filters/sorts server-side or request larger windows

Change:

- Backend should support media type, score, date, and size semantics if UI presents them as search controls.
- Alternatively, frontend should request larger candidate pools and label filters as “within returned results.”

Expected impact: Medium UX correctness impact.

Tradeoff: API/query-planning expansion.

### 17. Add a durable ingest/indexing queue

Change:

- Replace gateway `BackgroundTasks` dispatch with a durable queue/outbox and worker consumer.
- Move keyword-index rebuild to async/coalesced jobs.

Expected impact: High operational reliability impact.

Tradeoff: More infrastructure and worker-state complexity.

### 18. Harden public API surface before non-local deployment

Change:

- Add auth, rate limits, upload size limits, CORS defaults appropriate for deployment, and destructive-action protections.

Expected impact: High if deployed beyond localhost.

Tradeoff: Local development friction.

## 6. Open Questions and Unknowns

1. Should canonical scene identity be based on `media_id + scene_index`, a new UUID, `index_key`, or a manifest asset ID? The current system uses multiple competing identifiers.
2. Is filename-based scene identity intended only for the locked benchmark, or as a general API contract? Duplicate filenames make it unsafe as a global identifier.
3. Is deterministic ML fallback intended for production, or only for tests/dev? Current code can silently use fallback in non-strict modes.
4. Should negative queries require zero returned results, or zero returned results above a confidence threshold?
5. Is the Phase 7 baseline intended as a known-bad frozen reference or an actual quality gate? Its all-zero video/action slices suggest the distinction matters.
6. Should search filtering/sorting be corpus-wide semantics or only refinements over the current top-k response?
7. Is image-query retrieval quality expected to be benchmarked? The audited evaluation path is text-query only.
8. Should video-level search return parent videos, scenes, or both? Current implementation returns scenes only for videos.
9. Should fallback/weak caption quality be visible in API responses and ranking explanations?
10. Is Phase 8 candidate expansion still the active roadmap target? Some docs point to Phase 8 as next; other task docs mark Phase 8 reverted/not active.

---

## Appendix A — High-priority evidence summary

- Full vector scan and sort: `services/shared/semedia_shared/search_service.py:78-129`.
- Top-k truncation before fusion: `search_service.py:128-145`, `index_service.py:203-204`.
- Clamp-only score normalization/fusion: `search_service.py:23-26`, `ranking_service.py:13-14,128-145`.
- Tuple scene-key bug: `search_service.py:49-52`.
- Filename-based scene key: `search_service.py:43-48`; non-unique filename field: `models.py:31-34`.
- Scene DB/index/external identity split: `models.py:68-85`, `pipeline.py:120`, `search_service.py:43-60`, `frontend/src/types/api.ts:59-76`, `evaluate_search.py:117-123`.
- Caption retry/fallback and weak filtering: `caption_service.py:54-66,168-241`.
- Captions as keyword corpus: `index_service.py:51-93`.
- Global caption dedupe: `ranking_service.py:66-88`.
- Full keyword rebuild after processing/delete: `pipeline.py:49-55`, `gateway_api/app/main.py:217-222`.
- Evaluation metric duplicate sensitivity: `testing/evaluation/evaluate_search.py:18-45`.
- Negative-query saturation: `evaluate_search.py:66-78`.
- Strict validator optional in library path: `benchmark_validation.py:68-82`, `evaluate_search.py:14-15`.
- Evaluation text-only shape: `evaluate_search.py:126-167`, `run_evaluation.py:24-35,115-128`.
