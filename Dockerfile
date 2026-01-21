FROM python:3.12-slim

# --- Python runtime settings ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# --- System dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- Install Python dependencies ---
# Copy only dependency metadata first for better layer caching
COPY pyproject.toml ./

RUN pip install --no-cache-dir .

# --- Copy application code ---
COPY app ./app

# --- Runtime ---
# Render will inject PORT; local/docker-compose defaults to 8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
