import logging

from fastapi import APIRouter, Depends, Request, status
from src.core.database import get_db
from src.core.deps import get_request_id
from src.models.interfaces.schemas import IntakeRequest
from src.repositories.callback_repository import CallbackRepository
from src.repositories.idempotency_repository import IdempotencyRepository
from src.repositories.metadata_repository import MetadataRepository
from src.services.idempotency_guard import IdempotencyGuard
from src.services.intake_service import IntakeService
from src.services.metadata_service import MetadataService

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(get_request_id)],
)

logger = logging.getLogger(__name__)


@router.get("/ping")
def ping():
    # Uncomment only for testing global exception handling
    # raise ConfigError("boom")
    return {"status": "ok"}


@router.post("/intake", status_code=status.HTTP_202_ACCEPTED)
async def intake(
    request: IntakeRequest,
    http_request: Request,
    db=Depends(get_db),
):
    """
    Intake entrypoint.
    Responsibilities:
    - Extract metadata from HTTP headers via MetadataService
    - Resolve request_id
    - Wire dependencies
    - Delegate to IntakeService
    """
    metadata = await MetadataService.extract(http_request)

    guard = IdempotencyGuard(repo=IdempotencyRepository(db))

    service = IntakeService(
        idempotency=guard,
        callback_repo=CallbackRepository(db),
        metadata_repo=MetadataRepository(db),
    )

    return await service.intake(
        request_id=request.request_id,
        app_id=request.app_id,
        payload=request.payload,
        callback_url=request.callback_url,
        metadata=metadata,
    )
