FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/services/shared

WORKDIR /app

COPY services/gateway_api/requirements.txt /tmp/gateway-requirements.txt
COPY services/search_api/requirements.txt /tmp/search-requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/gateway-requirements.txt && \
    pip install -r /tmp/search-requirements.txt && \
    pip install pytest httpx

COPY services/shared /app/services/shared
COPY services/gateway_api /app/services/gateway_api
COPY services/media_worker /app/services/media_worker
COPY services/search_api /app/services/search_api
COPY testing/services /app/testing/services

CMD ["pytest", "/app/testing/services", "-q"]
