# src/api/routes/kyc.py

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.interfaces.kyc_interface.kyc_request_interface import KYCTriggerRequest
from src.models.interfaces.kyc_interface.kyc_response_interface import KYCTriggerResponse
from src.services.kyc_services.kyc_service import trigger_kyc_service
from src.utils.db_session import get_db 

router = APIRouter(prefix="/kyc", tags=["KYC_Intake"])


@router.post("/trigger", response_model=KYCTriggerResponse)
async def trigger_kyc(
    payload: KYCTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    attempt = await trigger_kyc_service(
        db=db,
        application_id=payload.applicant_id,
        idempotency_key=payload.idempotency_key,
    )

    return KYCTriggerResponse(
        attempt_id=attempt.id,
        kyc_status=attempt.status.value,
    )
