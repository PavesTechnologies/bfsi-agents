"""
AUTO-GENERATED FILE.

FastAPI application factory.

Responsibilities:
- create FastAPI app
- register routers
- configure middleware (later)

Do NOT put business logic here.
"""

# src/app.py

from fastapi import FastAPI
from redis import Redis

from src.api.routes import router
from src.api.middleware.idempotency import IdempotencyMiddleware
from src.repositories.idempotency_repository import RedisIdempotencyRepository


def create_app() -> FastAPI:
    app = FastAPI(title="kyc_agent", version="1.0.0")

    redis_client = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    redis_repo = RedisIdempotencyRepository(redis_client)

    app.state.redis_repo = redis_repo

    app.add_middleware(IdempotencyMiddleware, repository=redis_repo)

    app.include_router(router)

    return app
