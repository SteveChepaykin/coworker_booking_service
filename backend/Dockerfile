FROM python:3.11-slim AS builder

# Set environment variables
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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=development

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 --no-create-home app

# Set work directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
# Create scripts directory
RUN mkdir -p /app/scripts

# Copy application code
COPY . .
COPY scripts/ /app/scripts/
RUN ls -la /app/scripts
RUN ls -la /app

# Change ownership to non-root user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Run the application
CMD ["/app/scripts/start.sh"]