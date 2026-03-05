"""
API Routes for Orchestrator
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any

from src.services.pipeline_service import PipelineService

router = APIRouter()

class ApplicationTriggerRequest(BaseModel):
    raw_application: Dict[str, Any]


@router.get("/")
def health_check():
    return {"status": "ok", "service": "orchestrator"}


@router.post("/trigger_pipeline")
async def trigger_pipeline(request: ApplicationTriggerRequest):
    """
    Triggers the end-to-end pipeline given a raw application payload.
    """
    service = PipelineService()
    try:
        result = await service.execute_full_pipeline(
            raw_application=request.raw_application
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
