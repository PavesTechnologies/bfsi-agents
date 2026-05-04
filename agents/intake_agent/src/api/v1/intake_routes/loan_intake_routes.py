from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.dependencies.rate_limit import rate_limit_dependency
from src.models.interfaces.Loan_intake_interfaces import (
    LoanIntakeRequest,
    LoanIntakeResponse,
    OrchestratorTriggerRequest,
)
from src.services.intake_services import loan_intake_service
from src.services.intake_services.document_readiness import DocumentReadinessChecker
from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.utils.intake_database.db_session import get_db

router = APIRouter(prefix="/loan_intake", tags=["loan_intake"])


@router.get("/check", dependencies=[Depends(rate_limit_dependency)])
async def check_loan_intake_service(
    db: AsyncSession = Depends(get_db),
) -> str:
    service = LoanIntakeService(db)
    return await service.check()


@router.post("/submit_application", response_model=LoanIntakeResponse)
async def submit_loan_application(
    request: LoanIntakeRequest,
    db: AsyncSession = Depends(get_db),
) -> LoanIntakeResponse:
    service = LoanIntakeService(db)
    response = await service.submit_application(request)

    if isinstance(response, dict):
        return LoanIntakeResponse.model_validate(response)
    return response


@router.post("/trigger_orchestrator")
async def trigger_orchestrator(
    request: OrchestratorTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    # --- Document readiness gate ---
    try:
        application_uuid = UUID(request.application_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="application_id must be a valid UUID",
        )

    checker = DocumentReadinessChecker(db)
    result = await checker.check(application_uuid)
    if not result.ready:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Application is not ready to be processed. Please upload all required documents.",
                **result.to_detail(),
            },
        )

    # --- Forward to orchestrator ---
    settings = get_settings()
    url = f"{settings.ORCHESTRATOR_URL}/trigger_pipeline_async"
    payload = {
        "application_id": request.application_id,
        "raw_application": request.raw_application,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=15.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Orchestrator returned an error: {exc.response.text}",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Could not connect to Orchestrator at {url}: {str(exc)}",
            )