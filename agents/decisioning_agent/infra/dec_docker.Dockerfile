# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --upgrade pip && pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Enable in-project virtualenv (.venv inside /app)
RUN poetry config virtualenvs.in-project true

# Install dependencies (creates .venv)
RUN poetry install --no-root --no-interaction --no-ansi

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src /app/src

# Set PATH to use .venv
ENV PATH="/app/.venv/bin:$PATH"

# Ensure src package in /app is importable
ENV PYTHONPATH="/app"

USER appuser

EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]