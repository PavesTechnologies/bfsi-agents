import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from src.core.deps import db_client

router = APIRouter()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health")


@router.get("/live")
async def live():
    logger.info("health_live_check")
    return {"status": "alive"}


@router.get("/ready")
async def ready():
    logger.info("health_ready_check_started")

    try:
        if not db_client.ping():
            raise RuntimeError("db_unreachable")

        logger.info("health_ready_check_passed")
        return {"status": "ready"}

    except Exception as exc:
        logger.warning("health_ready_check_failed", exc_info=exc)

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )
