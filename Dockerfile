# ── Stage 1: Base image ───────────────────────────────────────
FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────
# Install only what we need
# --no-install-recommends keeps image small
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user ─────────────────────────────────────────────
# Create group and user
# -r = system user (no login shell, no home dir by default)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# ── Working directory ─────────────────────────────────────────
WORKDIR /app

# ── Layer caching — dependencies first ────────────────────────
# Copy ONLY dependency files first
# If these don't change → pip install layer is cached
# Even if your code changes → pip install NOT re-run
COPY pyproject.toml uv.lock ./

# Install uv for fast dependency installation
RUN pip install uv

# Install dependencies without project code
RUN uv export --no-dev --no-hashes --no-emit-project -o requirements.txt && \
    pip install -r requirements.txt

# ── Copy application code ─────────────────────────────────────
# This layer changes most often — keep it LAST
# Changes here don't invalidate the pip install layer above
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# ── Ownership ─────────────────────────────────────────────────
# Give appuser ownership of the app directory
RUN chown -R appuser:appgroup /app

# ── Switch to non-root user ───────────────────────────────────
# All subsequent commands run as appuser
# NOT as root
USER appuser
ENV PYTHONPATH=/app/src

# ── Port ──────────────────────────────────────────────────────
EXPOSE 8000

# ── Health check ──────────────────────────────────────────────
# Docker itself checks this every 30s
# If it fails 3 times → container marked unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Start command ─────────────────────────────────────────────
# Gunicorn manages worker processes
# UvicornWorker = each worker is async FastAPI compatible
# -w 4 = 4 workers (adjust based on CPU cores)
# --bind = listen on all interfaces port 8000
# No secrets here — they come from environment at runtime
CMD ["gunicorn", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "src.real_estate_backend.main:app"]