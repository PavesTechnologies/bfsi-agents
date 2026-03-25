"""
API Routes for the Disbursement Agent
"""

from fastapi import APIRouter, HTTPException, Request, status
from src.core.exceptions import (
    DuplicateRequestInProgressError,
    IdempotencyConflictError,
)
from src.core.request_context import resolve_correlation_id
from src.domain.entities import DisbursementRequest
from src.services.orchestrator import run_disbursement

router = APIRouter()


@router.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "disbursment_agent"}


@router.post("/disburse")
async def disburse(request: DisbursementRequest, http_request: Request):
    """
    Trigger the loan disbursement workflow.

    Accepts pre-resolved loan terms and returns a DisbursementReceipt
    with transfer details and repayment schedule.
    """
    try:
        correlation_id = resolve_correlation_id(
            http_request,
            None,
            request.application_id,
        )
        receipt = await run_disbursement(request, correlation_id)
        print(receipt)
        return receipt
    except IdempotencyConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateRequestInProgressError as e:
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
