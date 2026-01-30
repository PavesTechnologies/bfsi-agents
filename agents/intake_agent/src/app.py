import logging
from fastapi import FastAPI, Request

from fastapi.responses import JSONResponse
from src.core.logging import setup_logging, request_id_ctx

from src.api.v1.routes import router
from src.core.database import engine
from src.models.idempotency import Base
from src.api.v1.health import router as health_router
from src.core.exceptions import BaseAgentException
from src.api.v1.intake_routes import loan_intake_routes
from src.core.container import job_executor



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
    app.include_router(loan_intake_routes.router)
    

    # -------------------------
    # LIFECYCLE EVENTS
    # -------------------------
    @app.on_event("startup")
    async def startup_event():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @app.on_event("shutdown")
    async def shutdown_event():
        await engine.dispose()

    return app
