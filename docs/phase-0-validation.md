# Phase 0 Validation

This phase validates the machine and runtime before backend AI processing work begins.

## Required Runtime

- Python 3.11.x
- FFmpeg on `PATH`
- PostgreSQL 16
- CUDA-capable NVIDIA GPU with 8 GB VRAM
- PyTorch with matching CUDA build
- `transformers`, `opencv-python-headless`, `scenedetect`, and `scikit-learn`

## Current Workspace Findings

Based on validation run on 2026-04-13:

- Python present: `3.13.5`
- `ffmpeg`: missing
- Installed Python packages available now: `numpy`, `PIL`
- Missing packages for Phase 0 benchmarking:
  - `torch`
  - `transformers`
  - `cv2`
  - `scenedetect`
  - `sklearn`

## Exit Criteria

- Validation script passes without failed checks.
- CLIP and BLIP-2 benchmark script runs on sample inputs.
- The team confirms whether native Windows is acceptable or if WSL2/Linux is required for BLIP-2 int8 setup.
- Redis and Celery are not part of the MVP environment gate.
