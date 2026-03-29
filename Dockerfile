# ── Stage 1: Builder ─────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies for native extensions (psycopg, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install ".[preview]"

# ── Stage 2: Runtime ─────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# System dependencies:
#   chromium        — Kaleido/Plotly static chart rendering
#   fonts-*         — TrueType fonts for headless text measurement
#   libpq-dev       — PostgreSQL client library for psycopg
#   libreoffice-impress — headless PPTX-to-PDF for thumbnail generation
#   poppler-utils   — PDF-to-PNG conversion (pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    fonts-dejavu-core \
    libpq-dev \
    libreoffice-impress \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_PATH=/usr/bin/chromium
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Non-root user for security
RUN useradd --create-home --shell /bin/bash deckforge
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Copy theme YAML files (ensure they are included even if src/ COPY missed them)
COPY src/deckforge/themes/data/ src/deckforge/themes/data/

RUN chown -R deckforge:deckforge /app
USER deckforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')"

CMD ["uvicorn", "deckforge.main:app", "--host", "0.0.0.0", "--port", "8000"]
