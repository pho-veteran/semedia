# Phase 4: Improve Caption Quality

**Date:** 2026-04-30  
**Status:** Complete  
**Goal:** Improve caption generation quality for both images and video scenes to fix the zero-baseline relevance metrics from Phase 1.

## Problem

Phase 1 baseline evaluation showed all relevance metrics at 0.0 because caption quality is too weak:
- `cat.jpg` captioned as "two golden retrievers"
- `mountain.jpg` captioned as "someone at a table with laptop"
- Generic captions like "a person" or "an image" provide no retrieval signal
- Video scenes from the same video often get identical captions despite different content

Current caption pipeline (`caption_service.py`) processes images one at a time (batched in Phase 2) but uses default BLIP/BLIP-2 inference settings with no quality validation or post-processing.

## Solution

Improve caption quality at three points without changing the storage model or adding new services:

1. **Model configuration tuning** - adjust BLIP/BLIP-2 inference parameters for more specific, accurate captions
2. **Caption post-processing** - add lightweight cleanup rules to catch obvious failures
3. **Quality validation with retry** - regenerate weak captions once with stricter settings

## Implementation

### 1. Add caption quality validation

**File:** `services/shared/semedia_shared/caption_service.py`

Add quality check function after existing caption generation:

```python
def _is_weak_caption(caption: str) -> bool:
    """Return True if caption is too generic or low-quality."""
    if not caption or len(caption.strip()) < 10:
        return True
    
    # Reject overly generic captions
    generic_patterns = [
        "an image",
        "a picture",
        "a photo",
        "something",
        "unclear",
    ]
    caption_lower = caption.lower().strip()
    if any(pattern in caption_lower for pattern in generic_patterns):
        return True
    
    # Reject single-word or two-word captions (too vague)
    if len(caption.split()) <= 2:
        return True
    
    return False
```

### 2. Add caption post-processing

**File:** `services/shared/semedia_shared/caption_service.py`

Add cleanup function:

```python
def _clean_caption(caption: str) -> str:
    """Normalize and clean generated caption."""
    if not caption:
        return ""
    
    # Normalize whitespace
    caption = " ".join(caption.split())
    
    # Remove trailing/leading punctuation artifacts
    caption = caption.strip(".,;: ")
    
    # Capitalize first letter
    if caption:
        caption = caption[0].upper() + caption[1:]
    
    # Ensure ends with period
    if caption and caption[-1] not in ".!?":
        caption += "."
    
    return caption
```

### 3. Tune BLIP/BLIP-2 generation parameters

**File:** `services/shared/semedia_shared/caption_service.py`

Update `generate_captions()` to use better generation settings:

**Current default settings:**
```python
outputs = model.generate(**inputs)
```

**New settings for quality:**
```python
outputs = model.generate(
    **inputs,
    max_length=50,           # Allow longer, more descriptive captions (was implicit 20)
    min_length=10,           # Prevent very short captions
    num_beams=5,             # Use beam search for better quality (was 1/greedy)
    length_penalty=0.8,      # Slight preference for longer captions
    repetition_penalty=1.2,  # Discourage repetitive phrases
    no_repeat_ngram_size=3,  # Prevent 3-gram repetition
)
```

These settings prioritize caption quality over speed, which aligns with the "quality first" constraint.

### 4. Add retry logic for weak captions

**File:** `services/shared/semedia_shared/caption_service.py`

Update `generate_captions()` to retry weak captions once:

```python
def generate_captions(
    settings,
    image_paths: list[str],
    model_name: str | None = None,
    device: str | None = None,
) -> list[str]:
    """Generate captions for a batch of images with quality validation and retry."""
    
    # ... existing model loading logic ...
    
    # First pass: generate captions with quality settings
    raw_captions = []
    for batch in _chunk_images(image_paths, batch_size=8):
        inputs = processor(images=batch, return_tensors="pt").to(device)
        outputs = model.generate(
            **inputs,
            max_length=50,
            min_length=10,
            num_beams=5,
            length_penalty=0.8,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3,
        )
        batch_captions = [processor.decode(output, skip_special_tokens=True) for output in outputs]
        raw_captions.extend(batch_captions)
    
    # Post-process and validate
    final_captions = []
    retry_indices = []
    
    for idx, caption in enumerate(raw_captions):
        cleaned = _clean_caption(caption)
        if _is_weak_caption(cleaned):
            retry_indices.append(idx)
            final_captions.append("")  # Placeholder for retry
        else:
            final_captions.append(cleaned)
    
    # Retry weak captions with stricter settings
    if retry_indices:
        logger.info("Retrying %d weak captions with stricter settings", len(retry_indices))
        retry_paths = [image_paths[idx] for idx in retry_indices]
        retry_images = [load_image_for_ml(path) for path in retry_paths]
        
        inputs = processor(images=retry_images, return_tensors="pt").to(device)
        outputs = model.generate(
            **inputs,
            max_length=60,           # Even longer for retry
            min_length=15,           # Higher minimum
            num_beams=8,             # More beams for better search
            length_penalty=1.0,      # Neutral length preference
            repetition_penalty=1.5,  # Stronger repetition penalty
            no_repeat_ngram_size=2,  # Stricter repetition control
        )
        retry_captions = [processor.decode(output, skip_special_tokens=True) for output in outputs]
        
        for retry_idx, caption in zip(retry_indices, retry_captions):
            cleaned = _clean_caption(caption)
            # Accept retry result even if still weak (avoid infinite loop)
            final_captions[retry_idx] = cleaned if cleaned else "Image content unclear."
    
    return final_captions
```

### 5. Add video scene caption deduplication check

**File:** `services/shared/semedia_shared/pipeline.py`

After generating scene captions in `_process_video()`, check for identical adjacent captions and flag them:

```python
def _process_video(settings, session: Session, media: MediaItem) -> None:
    # ... existing scene detection and caption generation ...
    
    # Generate captions for all scenes
    scene_captions = generate_captions(settings, keyframe_paths)
    
    # Detect and flag duplicate adjacent captions
    for i in range(1, len(scene_captions)):
        if scene_captions[i] == scene_captions[i - 1] and scene_captions[i]:
            logger.warning(
                "Adjacent scenes %d and %d have identical captions: %s",
                i - 1,
                i,
                scene_captions[i]
            )
            # Mark as low-quality by appending scene context
            scene_captions[i] = f"{scene_captions[i]} (scene {i + 1})"
    
    # ... rest of scene creation logic ...
```

This prevents identical captions from polluting search results when scenes are visually distinct.

## Testing Strategy

### Unit tests

**File:** `testing/services/test_caption_service.py` (new file)

Add tests for new caption quality functions:

```python
def test_is_weak_caption_rejects_generic():
    assert _is_weak_caption("an image")
    assert _is_weak_caption("a picture of something")
    assert _is_weak_caption("unclear")

def test_is_weak_caption_rejects_short():
    assert _is_weak_caption("cat")
    assert _is_weak_caption("a dog")
    assert _is_weak_caption("")

def test_is_weak_caption_accepts_descriptive():
    assert not _is_weak_caption("a golden retriever running in a park")
    assert not _is_weak_caption("sunset over the ocean with waves")

def test_clean_caption_normalizes_whitespace():
    assert _clean_caption("  a   dog  ") == "A dog."

def test_clean_caption_adds_period():
    assert _clean_caption("a cat on a table") == "A cat on a table."

def test_clean_caption_capitalizes():
    assert _clean_caption("golden retriever") == "Golden retriever."
```

### Integration tests

**File:** `testing/services/test_media_worker_pipeline.py`

Add test to verify caption quality after processing:

```python
def test_process_media_generates_quality_captions(tmp_path, monkeypatch):
    """Verify processed media has non-generic captions."""
    # ... setup test environment ...
    
    # Process test image
    process_media(settings, session, media.id)
    
    session.refresh(media)
    assert media.status == ProcessingStatus.COMPLETED
    assert media.caption
    assert len(media.caption.split()) > 2  # Not too short
    assert "an image" not in media.caption.lower()  # Not generic
    assert media.caption[-1] in ".!?"  # Proper punctuation
```

### Evaluation validation

**File:** `testing/evaluation/evaluate_search.py`

After Phase 4 implementation, rerun baseline evaluation:

```bash
docker compose run --rm service-tests python testing/evaluation/evaluate_search.py
```

Evaluation rule for Phase 4: judge caption-quality improvement only from caption-derived retrieval behavior. Do not use filenames as a retrieval signal, fallback, or scoring hint when evaluating this phase, because filename-based wins would hide whether caption quality actually improved.

Expected improvement:
- Precision@10 > 0.0 (at least some relevant items in top 10)
- Recall@10 > 0.0 (at least some relevant items retrieved)
- MRR > 0.0 (at least one relevant item ranked)
- NDCG@10 > 0.0 (some ranking quality signal)

Target: at least 2-3 of the 8 judged queries should return relevant items in top 10.

## Configuration

Add new caption generation settings to `services/shared/semedia_shared/config.py`:

```python
@dataclass
class Settings:
    # ... existing fields ...
    
    # Caption quality settings
    caption_max_length: int = 50
    caption_min_length: int = 10
    caption_num_beams: int = 5
    caption_retry_weak: bool = True
    caption_retry_num_beams: int = 8
```

Allow runtime tuning via environment variables:
- `CAPTION_MAX_LENGTH`
- `CAPTION_MIN_LENGTH`
- `CAPTION_NUM_BEAMS`
- `CAPTION_RETRY_WEAK`
- `CAPTION_RETRY_NUM_BEAMS`

## Files Changed

### Modified
- `services/shared/semedia_shared/caption_service.py` - add quality validation, post-processing, retry logic, tuned generation parameters
- `services/shared/semedia_shared/pipeline.py` - add video scene caption deduplication check
- `services/shared/semedia_shared/config.py` - add caption quality configuration fields

### Created
- `testing/services/test_caption_service.py` - unit tests for caption quality functions

### Updated
- `testing/services/test_media_worker_pipeline.py` - add caption quality integration test

## Success Criteria

- ✅ Caption generation uses quality-focused inference parameters
- ✅ Weak captions are detected and regenerated once
- ✅ Captions are cleaned and normalized
- ✅ Adjacent video scenes with identical captions are flagged
- ✅ Unit tests pass for quality validation functions
- ✅ Integration tests verify non-generic captions after processing
- ✅ Baseline evaluation shows improvement: at least one metric > 0.0
- ✅ No schema changes required
- ✅ Processing still completes successfully (quality first, speed secondary)

## Risks and Mitigations

**Risk:** Stricter generation settings increase processing time significantly.  
**Mitigation:** Measure processing time before/after. If unacceptable, reduce `num_beams` or disable retry for images (keep for video scenes only).

**Risk:** Retry logic causes runaway processing for consistently weak captions.  
**Mitigation:** Retry only once, accept result even if still weak to prevent loops.

**Risk:** Quality checks are too strict and reject valid captions.  
**Mitigation:** Start with conservative thresholds (10 chars, 2 words), tune based on false-positive rate in evaluation.

**Risk:** BLIP/BLIP-2 model limitations mean better settings still produce weak captions.  
**Mitigation:** Phase 4 is a low-cost first attempt. If metrics don't improve, Phase 5 can explore model replacement or second-pass refinement.

## Results

### Implementation delivered

- Extracted caption cleanup policy into `services/shared/semedia_shared/caption_cleanup_config.py`
- Refactored `services/shared/semedia_shared/caption_service.py` from a bloated alias-heavy file to a focused 274-line module
- Kept the weak-caption policy intentionally relaxed so slightly awkward but searchable captions are preserved
- Updated caption quality tests to match the relaxed policy
- Reprocessed the full 12-item corpus with the new cleanup rules

### Evaluation results

Live evaluation after reprocessing produced:

- Precision@10: 0.0889
- Recall@10: 0.8333
- MRR: 0.5262
- NDCG@10: 0.5692

This confirms Phase 4 moved retrieval quality off the zero baseline and substantially improved recall.

### Remaining failures

Per-query inspection showed the remaining weak queries are mostly caused by missing retrieval vocabulary in generated captions rather than cleanup logic:

- `cat` retrieves dog-heavy results because the corpus does not contain a matching cat caption
- `mountain landscape` has no useful keyword matches because captions lack `mountain` or `landscape`
- `person talking` has only weak keyword support
- `water` and `night scene` still depend mostly on vector similarity because captions omit those exact terms

## Next Steps After Phase 4

1. Improve caption semantic coverage, not cleanup strictness
2. Inspect whether retrieval should index light caption expansions such as scene synonyms
3. Consider a stronger caption model if current BLIP output remains too generic for hard queries
4. Continue ranking improvements only after caption vocabulary stops being the main bottleneck
