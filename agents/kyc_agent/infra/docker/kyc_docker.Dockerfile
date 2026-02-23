# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

# Copy installed dependencies from builder
COPY --from=builder /usr/local /usr/local

# Copy app code
COPY . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"]
