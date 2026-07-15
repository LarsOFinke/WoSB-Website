FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RBF_CONFIG_DIR=/app/config \
    RBF_ALEMBIC_CONFIG=/app/alembic.ini

WORKDIR /app

RUN addgroup --system --gid 10001 blackwater \
    && adduser --system --uid 10001 --ingroup blackwater --home /app blackwater

COPY pyproject.toml requirements.lock README.md alembic.ini ./
COPY migrations ./migrations
COPY config ./config
COPY src ./src
RUN pip install --upgrade pip \
    && pip install --requirement requirements.lock \
    && pip install --no-deps .

RUN mkdir -p /data/uploads \
    && chown -R blackwater:blackwater /app /data/uploads

USER blackwater
EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=4)"

CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
