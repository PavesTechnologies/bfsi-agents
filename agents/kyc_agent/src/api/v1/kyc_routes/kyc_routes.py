# src/api/routes/kyc.py

from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.interfaces.kyc_interface.kyc_request_interface import KYCTriggerRequest
from src.models.interfaces.kyc_interface.kyc_response_interface import KYCTriggerResponse
from src.services.kyc_services.kyc_service import KYCService
from src.utils.db_session import get_db 
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.db_session import get_db
# from fastapi import APIRouter, Depends, HTTPException
from src.services.kyc_services.kyc_orchestrator import KYCOrchestratorService

router = APIRouter(prefix="/kyc", tags=["KYC_Intake"])


# @router.post("/trigger", response_model=KYCTriggerResponse)
# async def trigger_kyc(
#     payload: KYCTriggerRequest,
#     db: AsyncSession = Depends(get_db),
# ):
#     service = KYCService(db)

#     response_payload = await service.trigger_kyc(
#         payload=payload.model_dump(mode="json"),
#     )

#     return KYCTriggerResponse(**response_payload)


# router = APIRouter(prefix="/v1/kyc", tags=["KYC"])

@router.post("/verify")
async def verify_identity(
    payload: KYCTriggerRequest, 
    service: KYCOrchestratorService = Depends()
):
    """
    Entry point for KYC Identity Agent (PRD Section 1.2).
    """
    try:
        result = await service.run_kyc_process(payload.model_dump(mode="json"))
        return result
    except Exception as e:
        # In production, log to OTel/Telemetry
        raise HTTPException(status_code=500, detail=str(e))