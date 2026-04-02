"""
API Routes for the Decisioning Agent
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.request_context import resolve_correlation_id
from src.domain.human_review_models import UnderwritingHumanReviewRequest
from src.domain.monitoring_models import MonitoringSnapshotRequest
from src.domain.underwriting_models import UnderwritingRequest
from src.services.underwriting_monitoring_service import UnderwritingMonitoringService
from src.services.underwriting_human_review_service import (
    UnderwritingHumanReviewService,
)
from src.services.underwriting_service import UnderwritingService
from src.utils.db_session import get_db


router = APIRouter(tags=["Underwriting"])


@router.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "decisioning_agent"}


@router.post("/underwrite")
async def underwrite(
    request: Request,
    payload: UnderwritingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the underwriting decision workflow.

    Accepts applicant financial data and the Experian credit report,
    runs the parallel risk evaluation graph, and returns the final
    decision (APPROVE, COUNTER_OFFER, or DECLINE).
    """
    try:
        correlation_id = resolve_correlation_id(
            request,
            payload_correlation_id=None,
            application_id=payload.application_id,
        )
        service = UnderwritingService(db)
        return await service.execute_underwriting(
            payload,
            correlation_id=correlation_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/underwriting-reviews")
async def submit_underwriting_review(
    payload: UnderwritingHumanReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = UnderwritingHumanReviewService(db)
        return await service.submit_review(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/underwriting-reviews/{application_id}")
async def get_latest_underwriting_review(
    application_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = UnderwritingHumanReviewService(db)
        return await service.get_latest_review(application_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring-snapshots")
async def create_monitoring_snapshot(
    payload: MonitoringSnapshotRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = UnderwritingMonitoringService(db)
        return await service.generate_snapshot(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring-snapshots/{segment_key}")
async def get_latest_monitoring_snapshot(
    segment_key: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = UnderwritingMonitoringService(db)
        return await service.get_latest_snapshot(segment_key)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
