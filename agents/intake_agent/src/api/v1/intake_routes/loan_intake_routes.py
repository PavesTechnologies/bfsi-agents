from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.intake_services import loan_intake_service
from src.utils.intake_database.db_session import get_db
from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest, LoanIntakeResponse
from src.dependencies.rate_limit import rate_limit_dependency
router = APIRouter(prefix="/loan_intake", tags=["loan_intake"])

@router.get("/check",dependencies=[Depends(rate_limit_dependency)])
async def check_loan_intake_service(
    db: AsyncSession = Depends(get_db)
    ) -> str:
    service = LoanIntakeService(db)
    return await service.check()

@router.post("/submit_application", response_model=LoanIntakeResponse)
async def submit_loan_application(
    request: LoanIntakeRequest,
    db: AsyncSession = Depends(get_db)
) -> LoanIntakeResponse:
    service = LoanIntakeService(db)
    response = await service.submit_application(request)
    
    # Handle dict response from idempotency cache
    if isinstance(response, dict):
        return LoanIntakeResponse.model_validate(response)
    return response