FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/services/shared

ARG INSTALL_GPU_RUNTIME=0
ARG PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cu130

WORKDIR /app/services/media_worker

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY services/media_worker/requirements.txt /tmp/requirements.txt
COPY services/media_worker/requirements.gpu.txt /tmp/requirements.gpu.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt && \
    if [ "$INSTALL_GPU_RUNTIME" = "1" ]; then \
      pip install torch==2.10.0 --index-url "$PYTORCH_INDEX_URL" && \
      pip install -r /tmp/requirements.gpu.txt; \
    else \
      pip install torch; \
    fi

COPY services/shared /app/services/shared
COPY services/media_worker /app/services/media_worker

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
