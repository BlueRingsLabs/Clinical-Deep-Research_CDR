# CDR API image
#
#   docker build -t cdr-api .
#   docker run --env-file .env -p 8000:8000 cdr-api
#
# Torch comes from the CPU wheel index. The default CUDA wheels add several GB
# for GPUs this image will never see.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu \
    CDR_DB_PATH=/app/data/cdr.db \
    CDR_ARTIFACT_PATH=/app/data/artifacts

WORKDIR /app

# curl: healthcheck. pango/harfbuzz: WeasyPrint (PDF export).
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      libpango-1.0-0 \
      libpangoft2-1.0-0 \
      libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install .

RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
  CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "cdr.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
