# ==================================
# Stage 1: Builder
# ==================================
FROM python:3.11-slim AS builder

RUN pip install poetry poetry-plugin-export
WORKDIR /app

COPY pyproject.toml poetry.lock* ./
COPY src/ ./src/

# Build the wheel file
RUN poetry build --format wheel

# Export dependencies to requirements.txt (optional, but cleaner for standard pip install)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# ==================================
# Stage 2: Runtime
# ==================================
FROM python:3.11-slim AS runtime

RUN useradd -m appuser
WORKDIR /app

# Copy requirements and the built wheel from the builder stage
COPY --from=builder /app/requirements.txt .
COPY --from=builder /app/dist/*.whl ./

# Install the app and its dependencies using standard pip (no poetry needed here)
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir *.whl && rm *.whl

USER appuser
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
