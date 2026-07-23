# ── Base image ─────────────────────────────────────────────────
FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    curl \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user ──────────────────────────────────────────────
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# ── Working directory ──────────────────────────────────────────
WORKDIR /app

# ── Dependencies first for layer caching ──────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ───────────────────────────────────────────
COPY . .

# ── Ownership ──────────────────────────────────────────────────
RUN chown -R appuser:appgroup /app

# ── Switch to non-root user ────────────────────────────────────
USER appuser

# ── Port ───────────────────────────────────────────────────────
EXPOSE 5000

# ── Health check ───────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/login || exit 1

# ── Start ──────────────────────────────────────────────────────
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]