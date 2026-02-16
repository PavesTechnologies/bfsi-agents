# src/api/routes/kyc.py

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.interfaces.kyc_interface.kyc_request_interface import KYCTriggerRequest
from src.models.interfaces.kyc_interface.kyc_response_interface import KYCTriggerResponse
from src.services.kyc_services.kyc_service import KYCService
from src.utils.db_session import get_db 
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.db_session import get_db

router = APIRouter(prefix="/kyc", tags=["KYC_Intake"])


@router.post("/trigger", response_model=KYCTriggerResponse)
async def trigger_kyc(
    payload: KYCTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    service = KYCService(db)

    response_payload = await service.trigger_kyc(
        payload=payload.model_dump(mode="json"),
    )

    return KYCTriggerResponse(**response_payload)