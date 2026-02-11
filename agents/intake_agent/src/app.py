import logging
from contextlib import asynccontextmanager  # <--- NEW IMPORT
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.logging import setup_logging, request_id_ctx
from src.api.v1.routes import router
from src.core.database import engine
from src.models.models import Base
from src.api.v1.health import router as health_router
from src.core.exceptions import BaseAgentException
from src.api.v1.intake_routes import loan_intake_routes
from src.core.container import job_executor
from src.api.v1.intake_routes import document_upload_routes
from src.api.v1.enrichment_routes import (
    usps_router,
    employer_router,
    phone_router,
    email_router,
)
from src.api.v1.human_in_loop import human_in_loop_routes
from src.api.v1.human_in_loop import human_in_loop_application_routes
from src.api.v1.loan_query import loan_query_routes

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
        logger.info("Shutdown: Disposing database engine")
        await engine.dispose()

    # -------------------------
    # App Definition
    # -------------------------
    app = FastAPI(
        title="intake_agent",
        description="Agent microservice: intake_agent",
        version="0.1.0",
        lifespan=lifespan,  # <--- CONNECTED HERE
    )

    # -------------------------
    # Middleware
    # -------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173", 
            "https://agenticaipaves.netlify.app" # Vite dev
        ],
        allow_credentials=False,
        allow_methods=["*"],        # enables OPTIONS
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
    
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_envelope": exc.detail # This will contain your list of ValidationResults
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        standardized_errors = []
        
        for error in exc.errors():
            # 1. Transform Pydantic 'loc' (tuple) into a readable string
            # e.g., ["body", "applicants", 0, "date_of_birth"] -> "applicants[0].date_of_birth"
            loc = error.get("loc", [])
            field_path = ".".join([str(x) for x in loc[1:]]) if len(loc) > 1 else "body"
            
            # 2. Map Pydantic 'type' to your ValidationReasonCode (or a generic one)
            error_type = error.get("type")
            reason_code = "INVALID_FORMAT" # Default
            
            if "date" in error_type:
                reason_code = "INVALID_DOB_FORMAT"
            elif "enum" in error_type:
                reason_code = "INVALID_ENUM_VALUE"
            elif "missing" in error_type:
                reason_code = "MISSING_REQUIRED_FIELD"

            standardized_errors.append({
                "field": field_path,
                "reason_code": reason_code,
                "message": error.get("msg").capitalize()
            })

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error_envelope": standardized_errors
            }
        )

    # -------------------------
    # Routers
    # -------------------------
    app.include_router(router)
    app.include_router(health_router)
    app.include_router(loan_intake_routes.router)
    app.include_router(document_upload_routes.router)
    app.include_router(usps_router)
    app.include_router(employer_router)
    app.include_router(phone_router)
    app.include_router(email_router)
    app.include_router(human_in_loop_routes.router)
    app.include_router(human_in_loop_application_routes.router)
    app.include_router(loan_query_routes.router)
    
    return app