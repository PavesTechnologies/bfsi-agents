"""
AUTO-GENERATED FILE.

FastAPI application factory.

Responsibilities:
- create FastAPI app
- register routers
- configure middleware (later)

Do NOT put business logic here.
"""

import uuid
import logging
from fastapi import FastAPI, Request

from fastapi.responses import JSONResponse
from src.core.logging import setup_logging, request_id_ctx
from src.api.v1.routes import router
from src.api.v1.health import router as health_router
from src.core.exceptions import BaseAgentException


logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="intake_agent",
        description="Agent microservice: intake_agent",
        version="0.1.0",
    )

    @app.exception_handler(BaseAgentException)
    async def base_agent_exception_handler(
        request: Request,
        exc: BaseAgentException,
    ):
        logger.exception("base_agent_exception_raised")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "request_id": request_id_ctx.get(),
            },
        )


    app.include_router(router)
    app.include_router(health_router)

    return app
