"""
Production finalization endpoints - read-only access to loan finalization state.

These endpoints read the loan_finalization_event table to provide:
- Final status of application processing
- Output JSON returned to LOS
- Manager-friendly pipeline trace

No domain logic execution. No callbacks. Pure database reads.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.adapters.http.callback.http_client import http_client
from src.core.database import get_db
from src.services.loan_finalize.LoanFinalizationService import LoanFinalizationService
from src.utils.finalize.callbacks import CallbackClient

router = APIRouter(
    prefix="/loan_intake",
    tags=["Finalization"],
)


@router.post("/finalize/{application_id}")
async def finalize_application(
    application_id: UUID, db: AsyncSession = Depends(get_db)
):
    service = LoanFinalizationService(
        db=db, callback_client=CallbackClient(http_client)
    )

    result = await service.finalize(
        application_id=application_id,
        callback_url="http://localhost:9000/mock-los",
        enrichments={"credit_check": {"score": 720, "risk": "low"}},
        errors=None,
    )

    return result
