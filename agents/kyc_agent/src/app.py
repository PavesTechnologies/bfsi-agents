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
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from src.core.logging import setup_logging
from src.core.exceptions import KYCBaseException, ComplianceHardFail
from src.core.telemetry import setup_telemetry
from src.api.routes import router


# test logging  
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="kyc_agent",
        description="Agent microservice: kyc_agent",
        version="0.1.0",
    )

    setup_telemetry(app)


    @app.exception_handler(KYCBaseException)
    async def kyc_exception_handler(request: Request, exc: KYCBaseException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "kyc_status": "FAIL" if isinstance(exc, ComplianceHardFail) else "ERROR",
                "reason": exc.message,
                "request_id": getattr(request.state, "request_id", "N/A")
            }
        )

    app.include_router(router)
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app
