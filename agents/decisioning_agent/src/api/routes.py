"""
API Routes for the Decisioning Agent
"""

from fastapi import APIRouter, HTTPException, Depends
from src.domain.underwriting_models import UnderwritingRequest
from src.utils.db_session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.underwriting_service import UnderwritingService


router = APIRouter(tags=["Underwriting"])


@router.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "decisioning_agent"}


@router.post("/underwrite")
async def underwrite(
    request: UnderwritingRequest, db: AsyncSession = Depends(get_db)
):
    """
    Trigger the underwriting decision workflow.

    Accepts applicant financial data and the Experian credit report,
    runs the parallel risk evaluation graph, and returns the final
    decision (APPROVE, COUNTER_OFFER, or DECLINE).
    """
    try:
        service = UnderwritingService(db)
        return await service.execute_underwriting(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
