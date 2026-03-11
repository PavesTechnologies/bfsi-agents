"""
API Routes for the Decisioning Agent
"""

from fastapi import APIRouter, HTTPException, Request, status
from src.core.exceptions import (
    DuplicateRequestInProgressError,
    IdempotencyConflictError,
)
from src.core.request_context import resolve_correlation_id
from src.domain.underwriting_models import UnderwritingRequest, UnderwritingResponse
from src.services.underwriting_service import run_underwriting

router = APIRouter()


@router.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "decisioning_agent"}


@router.post("/underwrite", response_model=UnderwritingResponse)
def underwrite(request: UnderwritingRequest, http_request: Request):
    """
    Trigger the underwriting decision workflow.

    Accepts applicant financial data and the Experian credit report,
    runs the parallel risk evaluation graph, and returns the final
    decision (APPROVE, COUNTER_OFFER, or DECLINE).
    """
    try:
        correlation_id = resolve_correlation_id(
            http_request,
            request.correlation_id,
            request.application_id,
        )
        result = run_underwriting(
            request.model_copy(update={"correlation_id": correlation_id})
        )
        return result
    except IdempotencyConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateRequestInProgressError as e:
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
