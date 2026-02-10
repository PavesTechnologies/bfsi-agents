from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.utils.intake_database.db_session import get_db
from src.services.loan_info_services.loan_query_service import LoanQueryService
from src.models.interfaces.loan_query_response_interface import LoanDetailsResponse

router = APIRouter(prefix="/loans", tags=["Loan Information"])

@router.get(
    "/{application_id}",
    response_model=LoanDetailsResponse
)
async def get_loan_details(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = LoanQueryService(db)
    loan = await service.get_full_loan_details(application_id)
    return loan
