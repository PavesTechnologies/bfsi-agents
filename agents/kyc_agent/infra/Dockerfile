# =========================
# Builder
# =========================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi



# =========================
# Runtime
# =========================
FROM python:3.11-slim

WORKDIR /app

RUN useradd -m appuser

# ✅ COPY dependencies (VERY IMPORTANT)
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# copy code
COPY ./src /app/src

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]