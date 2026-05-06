FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==1.8.3 && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --no-interaction --no-ansi

COPY . .

EXPOSE 8005

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "2"]
