"""
API Routes for the Decisioning Agent
"""

from fastapi import APIRouter, HTTPException
from src.domain.underwriting_models import UnderwritingRequest, UnderwritingResponse
from src.services.underwriting_service import run_underwriting

router = APIRouter()


@router.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "decisioning_agent"}


@router.post("/underwrite", response_model=UnderwritingResponse)
def underwrite(request: UnderwritingRequest):
    """
    Trigger the underwriting decision workflow.

    Accepts applicant financial data and the Experian credit report,
    runs the parallel risk evaluation graph, and returns the final
    decision (APPROVE, COUNTER_OFFER, or DECLINE).
    """
    try:
        result = run_underwriting(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
