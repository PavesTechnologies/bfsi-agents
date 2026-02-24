import logging
from contextlib import asynccontextmanager  # <--- NEW IMPORT

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.v1.health import router as health_router
from src.api.v1.human_in_loop import (
    human_in_loop_application_routes,
    human_in_loop_routes,
)
from src.api.v1.intake_routes import document_upload_routes, loan_intake_routes
from src.api.v1.loan_query import loan_query_routes
from src.api.v1.routes import router
from src.core.database import engine
from src.core.exceptions import BaseAgentException
from src.core.logging import request_id_ctx, setup_logging
from src.models.models import Base
from src.utils.intake_database.database_setup import dispose_engine

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    setup_logging()

    # -------------------------
    # Lifecycle Manager (Replaces on_event)
    # -------------------------
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # --- Startup Logic ---
        logger.info("Startup: Initializing database tables")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield  # Application runs here

        # --- Shutdown Logic ---
        logger.info("Shutdown: Disposing database engines")
        try:
            await engine.dispose()
            await dispose_engine()
        except Exception as e:
            logger.warning(f"Error disposing database engines: {e}")

    # -------------------------
    # App Definition
    # -------------------------
    app = FastAPI(
        title="intake_agent",
        description="Agent microservice: intake_agent",
        version="0.1.0",
        lifespan=lifespan,  # <--- CONNECTED HERE
        root_path="/intake",
    )

    # -------------------------
    # Middleware
    # -------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "https://agenticaipaves.netlify.app",  # Vite dev
        ],
        allow_credentials=False,
        allow_methods=["*"],  # enables OPTIONS
        allow_headers=["*"],
    )

    # -------------------------
    # Exception handling
    # -------------------------
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

    # -------------------------
    # Routers
    # -------------------------
    app.include_router(router)
    app.include_router(health_router)
    app.include_router(loan_intake_routes.router)
    app.include_router(document_upload_routes.router)
    # app.include_router(usps_router)
    # app.include_router(employer_router)
    # app.include_router(phone_router)
    # app.include_router(email_router)
    app.include_router(human_in_loop_routes.router)
    app.include_router(human_in_loop_application_routes.router)
    app.include_router(loan_query_routes.router)

    return app
