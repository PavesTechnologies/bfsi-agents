from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.intake_services import loan_intake_service
from src.utils.intake_database.db_session import get_db
from src.services.intake_services.loan_intake_service import LoanIntakeService
from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest, LoanIntakeResponse

router = APIRouter(prefix="/loan_intake", tags=["loan_intake"])

@router.get("/check")
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
    return await service.submit_application(request)