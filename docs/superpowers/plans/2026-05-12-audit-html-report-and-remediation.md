# Audit HTML Report and Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone dual-audience HTML version of the codebase audit report and implement safe high-priority fixes from the audit with tests.

**Architecture:** Generate a static self-contained report beside the Markdown source, then apply surgical fixes in small independent code/test tasks. High-risk architectural work from the audit is explicitly deferred rather than half-implemented.

**Tech Stack:** Markdown source, static HTML/CSS/vanilla JavaScript, Python/FastAPI/shared services, pytest, React/TypeScript, Docker Compose test runner.

---

## File Structure

### Create

- `docs/implementations/codebase-audit-report-2026-05-12.html`
  - Standalone HTML report derived from `docs/implementations/codebase-audit-report-2026-05-12.md`.

### Modify

- `services/shared/semedia_shared/search_service.py`
  - Fix `_stable_scene_key()` fallback tuple bug.
  - Add candidate-breadth support if implemented in Task 5.

- `services/search_api/app/main.py`
  - Bound `top_k` input to configured maximum.

- `frontend/src/types/api.ts`
  - Add `scene_index` and `scene_key` to `SearchResult`.

- `frontend/src/components/SearchResultCard.tsx`
  - Prefer `scene_index` for human scene labels if current code displays `scene_id`.

- `frontend/src/components/SearchResultGroup.tsx`
  - Prefer `scene_index` and `scene_key` for grouped scene labels/keys if current code displays or keys by `scene_id`.

- `testing/evaluation/evaluate_search.py`
  - Deduplicate retrieved identifiers before metric counting or fail clearly on duplicates; this plan uses dedupe-preserving-order.

### Test

- `testing/services/test_search_api.py`
  - Add/adjust backend tests for scene key fallback and `top_k` cap behavior.

- `testing/evaluation/test_evaluate_search.py`
  - Add metric tests for duplicate retrieved IDs.

- Existing frontend tests if present; otherwise rely on Dockerized frontend build/type check if available.

---

## Task 1: Generate standalone HTML report with Haiku

**Files:**
- Read: `docs/implementations/codebase-audit-report-2026-05-12.md`
- Create: `docs/implementations/codebase-audit-report-2026-05-12.html`

- [ ] **Step 1: Dispatch Haiku report builder**

Use a Haiku subagent with this exact assignment:

```text
Create a standalone static HTML report from `docs/implementations/codebase-audit-report-2026-05-12.md`.

Requirements:
- Write only `docs/implementations/codebase-audit-report-2026-05-12.html`.
- Do not edit application code, tests, configs, or Markdown source.
- Preserve all technical meaning and citations.
- Optimize for both executive and engineering audiences.
- Include: hero summary, risk/KPI cards, top findings, ranked remediation roadmap, sticky table of contents, deep technical sections, benchmark-rigor section, and appendix/evidence summary.
- Use self-contained HTML/CSS; optional tiny vanilla JS for collapsible sections is allowed.
- Do not use external CDNs, fonts, scripts, images, or generated URLs.
- Keep the report readable offline and printable.

Return a short summary of the layout and any transformations made.
```

Expected: Haiku creates the HTML file and reports no other file edits.

- [ ] **Step 2: Verify HTML artifact exists**

Run:

```powershell
Test-Path "docs/implementations/codebase-audit-report-2026-05-12.html"
```

Expected: `True`

- [ ] **Step 3: Check for external asset references**

Run:

```powershell
Select-String -Path "docs/implementations/codebase-audit-report-2026-05-12.html" -Pattern "https?://|//cdn|fonts.googleapis|<script src=|<link rel=\"stylesheet\"" -CaseSensitive:$false
```

Expected: no matches.

- [ ] **Step 4: Check required report sections**

Run:

```powershell
Select-String -Path "docs/implementations/codebase-audit-report-2026-05-12.html" -Pattern "System Overview|Top Findings|Improvement Recommendations|Benchmark|Evidence|Open Questions" -CaseSensitive:$false
```

Expected: matches for each required concept.

---

## Task 2: Fix scene_key fallback and bound top_k

**Files:**
- Modify: `services/shared/semedia_shared/search_service.py:43-52`
- Modify: `services/search_api/app/main.py:54-63,129-159`
- Test: `testing/services/test_search_api.py`

- [ ] **Step 1: Write failing scene key fallback test**

Add this test to `testing/services/test_search_api.py` near existing search serialization tests:

```python
def test_stable_scene_key_fallback_is_string():
    from semedia_shared.search_service import _stable_scene_key

    scene_key = _stable_scene_key({"scene_id": 42, "original_filename": "", "scene_index": None})

    assert scene_key == "scene:42"
    assert isinstance(scene_key, str)
```

- [ ] **Step 2: Run scene key test to verify it fails**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/services/test_search_api.py::test_stable_scene_key_fallback_is_string -v
```

Expected: FAIL because the current function returns `("scene:42",)`.

- [ ] **Step 3: Implement minimal scene key fix**

Change `services/shared/semedia_shared/search_service.py`:

```python
def _stable_scene_key(item: dict) -> str | None:
    original_filename = item.get("original_filename")
    scene_index = item.get("scene_index")
    if original_filename and scene_index is not None:
        return f"scene:{original_filename}:{scene_index}"

    scene_id = item.get("scene_id")
    if scene_id is None:
        return None
    return f"scene:{scene_id}"
```

- [ ] **Step 4: Run scene key test to verify it passes**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/services/test_search_api.py::test_stable_scene_key_fallback_is_string -v
```

Expected: PASS.

- [ ] **Step 5: Write top_k cap tests**

Add tests to `testing/services/test_search_api.py` for `_coerce_positive_top_k` behavior. Use direct import if existing tests already import from `services.search_api.app.main`; otherwise follow existing import style in the file.

```python
def test_coerce_positive_top_k_caps_to_max_results(search_env):
    from services.search_api.app.main import _coerce_positive_top_k

    assert _coerce_positive_top_k(9999) == search_env.settings.search_max_results


def test_coerce_positive_top_k_keeps_valid_small_value(search_env):
    from services.search_api.app.main import _coerce_positive_top_k

    assert _coerce_positive_top_k(3) == 3
```

If `search_env` is not available in this test file, use the existing settings fixture name from `testing/services/conftest.py` after inspecting it.

- [ ] **Step 6: Run top_k tests to verify they fail**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/services/test_search_api.py::test_coerce_positive_top_k_caps_to_max_results testing/services/test_search_api.py::test_coerce_positive_top_k_keeps_valid_small_value -v
```

Expected: first test FAILS because top_k is currently unbounded.

- [ ] **Step 7: Implement top_k cap**

Change `_coerce_positive_top_k` in `services/search_api/app/main.py` to use settings:

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
    return min(top_k, settings.search_max_results)
```

- [ ] **Step 8: Run targeted backend tests**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/services/test_search_api.py::test_stable_scene_key_fallback_is_string testing/services/test_search_api.py::test_coerce_positive_top_k_caps_to_max_results testing/services/test_search_api.py::test_coerce_positive_top_k_keeps_valid_small_value -v
```

Expected: PASS.

---

## Task 3: Align frontend search result scene fields

**Files:**
- Modify: `frontend/src/types/api.ts:59-76`
- Modify: `frontend/src/components/SearchResultCard.tsx`
- Modify: `frontend/src/components/SearchResultGroup.tsx`

- [ ] **Step 1: Update SearchResult type**

Change `frontend/src/types/api.ts` `SearchResult` to include backend fields:

```ts
export interface SearchResult {
  media_id: number
  scene_id: number | null
  scene_index: number | null
  scene_key: string | null
  media_type: MediaType
  result_type: 'image' | 'video_scene'
  original_filename: string
  score: number
  vector_score: number
  keyword_score: number
  caption: string
  file_url: string
  thumbnail_url: string
  file_size: number
  created_at: string
  start_time: number | null
  end_time: number | null
  explanation: SearchResultExplanation
}
```

- [ ] **Step 2: Prefer scene_index for display labels**

In `frontend/src/components/SearchResultCard.tsx`, replace scene label logic that displays `scene_id` with this pattern:

```ts
const sceneLabel = result.scene_index !== null && result.scene_index !== undefined
  ? `Scene ${result.scene_index + 1}`
  : result.scene_id !== null
    ? `Scene ${result.scene_id}`
    : 'Scene'
```

Use `sceneLabel` anywhere the card currently displays `Scene #${result.scene_id}` or equivalent.

- [ ] **Step 3: Prefer scene_key for grouped scene React keys**

In `frontend/src/components/SearchResultGroup.tsx`, use a key helper near the component body:

```ts
function sceneRenderKey(scene: SearchResult): string {
  if (scene.scene_key) {
    return scene.scene_key
  }
  if (scene.scene_id !== null) {
    return `scene:${scene.scene_id}`
  }
  return `media:${scene.media_id}:start:${scene.start_time ?? 'unknown'}`
}
```

Use `sceneRenderKey(scene)` for preview/hidden scene list keys.

- [ ] **Step 4: Prefer scene_index for grouped labels**

In `frontend/src/components/SearchResultGroup.tsx`, use this label pattern for each scene:

```ts
const sceneLabel = scene.scene_index !== null && scene.scene_index !== undefined
  ? `Scene ${scene.scene_index + 1}`
  : scene.scene_id !== null
    ? `Scene ${scene.scene_id}`
    : 'Scene'
```

Use `sceneLabel` anywhere the grouped UI currently displays a DB scene id as the user-facing scene number.

- [ ] **Step 5: Run frontend verification through Docker**

Run:

```powershell
docker compose run --rm frontend npm run build
```

Expected: TypeScript/Vite build succeeds.

If the `frontend` service does not support running npm commands directly, run:

```powershell
docker compose up -d --build frontend
```

Expected: frontend image builds successfully.

---

## Task 4: Harden evaluation duplicate handling

**Files:**
- Modify: `testing/evaluation/evaluate_search.py:18-45,165-167`
- Test: `testing/evaluation/test_evaluate_search.py`

- [ ] **Step 1: Write failing duplicate metric test**

Add this test to `testing/evaluation/test_evaluate_search.py` near existing `compute_metrics` tests:

```python
def test_compute_metrics_deduplicates_retrieved_ids_preserving_order():
    metrics = compute_metrics({"media:1", "media:2"}, ["media:1", "media:1", "media:2"], k=3)

    assert metrics["precision@3"] == 2 / 3
    assert metrics["recall@3"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["ndcg@3"] < 1.0
```

- [ ] **Step 2: Run duplicate metric test to verify it fails**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/evaluation/test_evaluate_search.py::test_compute_metrics_deduplicates_retrieved_ids_preserving_order -v
```

Expected: FAIL because duplicates are currently counted as separate hits.

- [ ] **Step 3: Add order-preserving dedupe helper**

In `testing/evaluation/evaluate_search.py`, add this helper above `compute_metrics`:

```python
def _dedupe_preserving_order(values: list[object]) -> list[object]:
    deduped: list[object] = []
    seen: set[object] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
```

- [ ] **Step 4: Use deduped retrieved IDs in metrics**

Change `compute_metrics()` to start with:

```python
def compute_metrics(relevant_ids: set[object], retrieved_ids: list[object], k: int = 10) -> dict[str, float]:
    retrieved_ids = _dedupe_preserving_order(retrieved_ids)
    top_k = retrieved_ids[:k]
    hits = sum(1 for item_id in top_k if item_id in relevant_ids)
```

Leave the rest of the metric math unchanged.

- [ ] **Step 5: Run duplicate metric test**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/evaluation/test_evaluate_search.py::test_compute_metrics_deduplicates_retrieved_ids_preserving_order -v
```

Expected: PASS.

- [ ] **Step 6: Run evaluation tests**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/evaluation/test_evaluate_search.py -v
```

Expected: PASS.

---

## Task 5: Add optional candidate breadth before fusion

**Files:**
- Modify: `services/shared/semedia_shared/config.py`
- Modify: `services/shared/semedia_shared/search_service.py:139-154`
- Test: `testing/services/test_search_api.py` or `testing/services/test_ranking_service.py`

- [ ] **Step 1: Inspect existing settings pattern**

Read `services/shared/semedia_shared/config.py` and confirm search settings are named and parsed like:

```python
search_max_results: int
search_max_per_media: int
search_vector_weight: float
search_keyword_weight: float
```

Expected: these settings exist and are used by search/ranking.

- [ ] **Step 2: Write failing candidate breadth test**

Add a focused unit test that monkeypatches `_vector_results`, `_keyword_results`, and `rank_candidates` in `semedia_shared.search_service` to prove `search_text()` asks retrieval branches for a wider candidate pool than final `top_k`.

Use this shape, adapting import style to the test file:

```python
def test_search_text_uses_candidate_breadth_before_final_limit(monkeypatch, search_env):
    from semedia_shared import search_service

    calls = []

    def fake_vector_results(settings, session, query_embedding, top_k):
        calls.append(("vector", top_k))
        return []

    def fake_keyword_results(settings, session, query_text, top_k):
        calls.append(("keyword", top_k))
        return []

    def fake_rank_candidates(settings, candidates, *, query_text, query_mode, limit):
        calls.append(("rank", limit))
        return []

    monkeypatch.setattr(search_service, "_vector_results", fake_vector_results)
    monkeypatch.setattr(search_service, "_keyword_results", fake_keyword_results)
    monkeypatch.setattr(search_service, "rank_candidates", fake_rank_candidates)
    monkeypatch.setattr(search_env.settings, "search_candidate_multiplier", 3, raising=False)

    search_service.search_text(search_env.settings, search_env.session, "birds", [0.1, 0.2], top_k=5)

    assert ("vector", 15) in calls
    assert ("keyword", 15) in calls
    assert ("rank", 5) in calls
```

- [ ] **Step 3: Run candidate breadth test to verify it fails**

Run the exact test path/name used in Step 2:

```powershell
docker compose --profile test run --rm service-tests pytest testing/services/test_search_api.py::test_search_text_uses_candidate_breadth_before_final_limit -v
```

Expected: FAIL because search currently asks both retrieval branches for only final `limit`.

- [ ] **Step 4: Add candidate multiplier setting**

Add to `services/shared/semedia_shared/config.py` near other search settings:

```python
search_candidate_multiplier: int = Field(default=3, alias="SEARCH_CANDIDATE_MULTIPLIER")
```

If the settings class uses a different exact pattern, follow the existing syntax but keep the field name and alias above.

- [ ] **Step 5: Use candidate breadth in text search only**

Change `search_text()` in `services/shared/semedia_shared/search_service.py`:

```python
def search_text(settings, session: Session, query_text: str, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    limit = top_k or settings.search_max_results
    candidate_multiplier = max(1, int(getattr(settings, "search_candidate_multiplier", 1)))
    candidate_limit = limit * candidate_multiplier
    vector_results = _normalize_scores(_vector_results(settings, session, query_embedding, candidate_limit))
    keyword_results = _normalize_scores(_keyword_results(settings, session, query_text, candidate_limit))
    candidates = merge_candidates(vector_results, keyword_results)
    ranked = rank_candidates(settings, candidates, query_text=query_text, query_mode="text", limit=limit)

    return [
        _serialize_ranked_result(item, query_text=query_text, query_mode="text")
        for item in ranked[:limit]
    ]
```

Do not change `search_image()` in this task.

- [ ] **Step 6: Run candidate breadth test**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/services/test_search_api.py::test_search_text_uses_candidate_breadth_before_final_limit -v
```

Expected: PASS.

- [ ] **Step 7: Run search service tests**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/services/test_search_api.py testing/services/test_ranking_service.py -v
```

Expected: PASS.

---

## Task 6: Final verification and review

**Files:**
- Review all changed files from Tasks 1-5.

- [ ] **Step 1: Show working tree status**

Run:

```powershell
git status --short
```

Expected: includes the HTML report, design spec, plan, and any code/test files changed by completed tasks. Existing untracked `CLAUDE.md` may still appear and should not be staged unless explicitly requested.

- [ ] **Step 2: Run targeted backend/evaluation verification**

Run:

```powershell
docker compose --profile test run --rm service-tests pytest testing/services/test_search_api.py testing/services/test_ranking_service.py testing/evaluation/test_evaluate_search.py -v
```

Expected: PASS.

- [ ] **Step 3: Run frontend verification if frontend files changed**

Run:

```powershell
docker compose run --rm frontend npm run build
```

Expected: PASS.

If that command is unsupported by the compose service, run:

```powershell
docker compose up -d --build frontend
```

Expected: frontend image builds successfully.

- [ ] **Step 4: Verify HTML remains self-contained**

Run:

```powershell
Select-String -Path "docs/implementations/codebase-audit-report-2026-05-12.html" -Pattern "https?://|//cdn|fonts.googleapis|<script src=|<link rel=\"stylesheet\"" -CaseSensitive:$false
```

Expected: no matches.

- [ ] **Step 5: Summarize completed and deferred work**

Report:

```text
Completed:
- HTML report generated at docs/implementations/codebase-audit-report-2026-05-12.html
- Scene key fallback fixed and tested
- top_k cap added and tested
- Frontend search result type aligned with backend scene fields
- Evaluation metrics dedupe duplicate retrieved IDs
- Candidate breadth before text fusion added if Task 5 completed

Deferred:
- Canonical scene identity migration
- ANN/vector index
- Durable processing queue
- Full benchmark ID migration
- Full score calibration project
```

Do not claim a task completed unless its verification command passed.
