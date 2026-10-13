# ==========================================
# Stage 1: Builder
# ==========================================

FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==========================================
# Stage 2: Production
# ==========================================

FROM python:3.12-slim AS production

WORKDIR /app

# Create a non-root user
RUN useradd --create-home --shell /usr/sbin/nologin appuser

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application files
COPY app/ ./app/

# Create a writable directory for the SQLite database
RUN mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Store the SQLite database in a directory suitable for a mounted volume.
ENV DATABASE_PATH=/app/data/cloudops.db

# Use a non-root user
USER appuser

# Flask application port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/')" || exit 1

# Start the application
CMD ["sh", "-c", "python -m app.seed && exec python -m flask --app app.app run --host=0.0.0.0 --port=5000"]