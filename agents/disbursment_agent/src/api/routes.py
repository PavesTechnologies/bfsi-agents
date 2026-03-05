"""
API Routes for the Disbursement Agent
"""

from fastapi import APIRouter, HTTPException
from src.domain.entities import DisbursementRequest
from src.services.orchestrator import run_disbursement

router = APIRouter()


@router.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "disbursment_agent"}


@router.post("/disburse")
def disburse(request: DisbursementRequest):
    """
    Trigger the loan disbursement workflow.

    Accepts the output of the Decisioning Agent and returns
    a DisbursementReceipt with transfer details and repayment schedule.
    """
    try:
        receipt = run_disbursement(request)
        return receipt
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
