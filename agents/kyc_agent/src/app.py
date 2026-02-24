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

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis import Redis

from src.api.routes import router
from src.api.v1.kyc_routes import kyc_routes
from src.core.exceptions import ComplianceHardFail, KYCBaseException
from src.core.logging import setup_logging
from src.core.telemetry import setup_telemetry
from src.repositories.idempotency_repository import RedisIdempotencyRepository

load_dotenv()
# test logging
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="kyc_agent",
        description="Agent microservice: kyc_agent",
        version="0.1.0",
        root_path="/kyc",
    )

    setup_telemetry(app)

    @app.exception_handler(KYCBaseException)
    async def kyc_exception_handler(request: Request, exc: KYCBaseException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "kyc_status": "FAIL"
                if isinstance(exc, ComplianceHardFail)
                else "ERROR",
                "reason": exc.message,
                "request_id": getattr(request.state, "request_id", "N/A"),
            },
        )

    redis_client = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    redis_repo = RedisIdempotencyRepository(redis_client)

    app.state.redis_repo = redis_repo

    # app.add_middleware(IdempotencyMiddleware, repository=redis_repo)

    app.include_router(router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    app.include_router(kyc_routes.router)

    return app
