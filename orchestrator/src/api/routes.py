"""
API Routes for Orchestrator
"""

from fastapi import APIRouter, HTTPException

from src.models.pipeline import (
    ApplicationTriggerRequest,
    ConfirmApprovalRequest,
    ResumeWithOfferRequest,
)
from src.services.pipeline_service import PipelineService

router = APIRouter()


@router.get("/")
def health_check():
    return {"status": "ok", "service": "orchestrator"}


@router.post("/trigger_pipeline")
async def trigger_pipeline(request: ApplicationTriggerRequest):
    """
    Triggers the pipeline until a user decision is required or it is declined.
    """
    service = PipelineService()
    try:
        result = await service.execute_until_decision(
            application_id=request.application_id,
            raw_application=request.raw_application,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/select_counter_offer")
async def select_counter_offer(request: ResumeWithOfferRequest):
    """Resume disbursement after the user chooses a counter offer."""
    service = PipelineService()
    try:
        return await service.resume_after_counter_offer_selection(
            application_id=request.application_id,
            selected_offer_id=request.selected_offer_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/confirm_approval")
async def confirm_approval(request: ConfirmApprovalRequest):
    """Resume or cancel an approved application based on user confirmation."""
    service = PipelineService()
    try:
        if not request.accepted:
            return service.cancel_pending_application(request.application_id)
        return await service.resume_after_approval_confirmation(
            application_id=request.application_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
