import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.db.base import (
    admin_engine,
    decisioning_engine,
    disbursement_engine,
    intake_engine,
    kyc_engine,
)
from src.db.base import Base
from src.routers.auth import router as auth_router
from src.routers.applications import router as applications_router
from src.routers.config import router as config_router
from src.routers.internal import router as internal_router
from src.routers.review_queue import router as review_queue_router
from src.routers.reports import router as reports_router

settings = get_settings()
logger = logging.getLogger(__name__)
_testing = os.getenv("TESTING", "0") == "1"


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not _testing:
            logger.info("Startup: creating admin_db tables if not exist")
            async with admin_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        logger.info("Startup complete")

        yield

        logger.info("Shutdown: disposing database engines")
        for engine in (
            admin_engine,
            intake_engine,
            kyc_engine,
            decisioning_engine,
            disbursement_engine,
        ):
            await engine.dispose()

    app = FastAPI(
        title="Admin Service",
        description="Lender portal backend — auth, human review queue, config, reports",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(auth_router)
    app.include_router(applications_router)
    app.include_router(config_router)
    app.include_router(internal_router)
    app.include_router(review_queue_router)
    app.include_router(reports_router)

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "service": settings.service_name}

    return app
