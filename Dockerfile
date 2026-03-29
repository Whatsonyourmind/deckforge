FROM python:3.12-slim

# Install system dependencies:
# - fonts-liberation, fonts-dejavu-core: TrueType fonts for headless text measurement
# - libpq-dev: PostgreSQL client library for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    fonts-dejavu-core \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.deckforge.main:app", "--host", "0.0.0.0", "--port", "8000"]
