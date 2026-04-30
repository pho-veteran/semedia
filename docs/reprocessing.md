# Reprocessing Media

After schema migrations or processing pipeline improvements, existing media items may need to be reprocessed to populate new fields or regenerate outputs with updated logic.

## Overview

The reprocessing utility (`testing/reprocess_media.py`) allows you to regenerate processing outputs for existing media items. It:

- Runs pending database migrations before reprocessing
- Supports filtering by processing status
- Supports explicit media ID selection
- Processes media in configurable batches to prevent memory issues
- Is idempotent and resumable (safe to run multiple times)
- Reports summary statistics

## Usage

### Reprocess all completed media

```bash
python testing/reprocess_media.py
```

This reprocesses all media with `status=completed` (the default).

### Reprocess specific media IDs

```bash
python testing/reprocess_media.py --media-ids 1 5 10 23
```

### Reprocess failed media

```bash
python testing/reprocess_media.py --status failed
```

### Configure batch size

```bash
python testing/reprocess_media.py --batch-size 10
```

Default batch size is 50. Smaller batches reduce memory usage but increase overhead.

## When to Reprocess

**After schema migrations:**
- Phase 2 added `retrieval_text`, multi-frame fields, and `best_frame_index`
- Reprocessing populates these fields for existing media

**After pipeline improvements:**
- Updated caption models
- Updated scene detection thresholds
- Updated embedding models

**After fixing processing bugs:**
- Reprocess media that failed due to the bug

## What Gets Regenerated

**For images:**
- Caption
- Embedding
- `retrieval_text`
- `index_key`

**For videos:**
- Duration
- Scene detection (with current adaptive thresholds)
- 3 keyframes per scene (at 10%, 50%, 90% of scene duration)
- 3 thumbnails per scene
- 3 captions per scene
- 3 embeddings per scene
- Scene-level aggregated caption, embedding, and `retrieval_text`
- Video-level aggregated caption and `retrieval_text`
- `index_key` for media and scenes

Old scene frames and thumbnails are deleted before regeneration.

## Running in Docker

From the `Semedia/` directory:

```bash
docker compose run --rm service-tests python testing/reprocess_media.py --status completed
```

## Exit Codes

- `0`: All media reprocessed successfully
- `1`: One or more media items failed to reprocess

## Example Output

```
Total media processed: 42
Successful: 40
Failed: 2
Failed media IDs: 15, 23
```

## Notes

- Reprocessing calls the same `process_media()` function used during upload
- The script is safe to interrupt (Ctrl+C) and resume later
- Migrations run automatically before reprocessing starts
- Batch processing prevents memory issues with large media libraries
- Failed items are logged but do not stop processing of remaining items
