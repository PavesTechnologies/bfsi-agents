# -------- Base image --------
FROM python:3.11-slim AS runtime

# -------- System deps --------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -------- Create non-root user --------
RUN useradd -m appuser
WORKDIR /app

# -------- Copy dependency files --------
COPY pyproject.toml poetry.lock* ./

# -------- Install Poetry --------
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main --no-root

# -------- Copy application --------
COPY src ./src

# -------- Switch user --------
USER appuser

# -------- Expose port --------
EXPOSE 8000

# -------- Run app --------
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
