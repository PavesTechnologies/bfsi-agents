"""
AUTO-GENERATED FILE.

FastAPI application factory.

Responsibilities:
- create FastAPI app
- register routers
- configure middleware (later)

Do NOT put business logic here.
"""
import logging
# src/app.py

from fastapi import FastAPI
from redis import Redis

from src.core.logging import setup_logging
from src.api.routes import router
from src.api.middleware.idempotency import IdempotencyMiddleware
from src.repositories.idempotency_repository import RedisIdempotencyRepository


# test logging  
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="kyc_agent",
        description="Agent microservice: kyc_agent",
        version="0.1.0",
    )

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
