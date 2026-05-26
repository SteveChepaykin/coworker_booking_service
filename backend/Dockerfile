FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
    
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /tmp/pip-cache

COPY requirements.txt requirements-dev.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "pydantic[email]"

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=development
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 --no-create-home app

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
RUN mkdir -p /app/scripts

COPY . .
COPY scripts/ /app/scripts/
RUN ls -la /app/scripts
RUN ls -la /app

RUN sed -i 's/\r$//' /app/scripts/*.sh && \
    chmod +x /app/scripts/*.sh

RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["/app/scripts/start.sh"]