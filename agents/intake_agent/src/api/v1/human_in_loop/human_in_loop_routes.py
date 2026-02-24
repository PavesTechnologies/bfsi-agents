from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.interfaces.human_in_loop_interface import (
    HumanInLoopRequest,
    HumanInLoopResponse,
)
from src.services.human_in_loop_services.human_in_loop_service import HumanInLoopService
from src.utils.intake_database.db_session import get_db

router = APIRouter(prefix="/human-review", tags=["Human In Loop"])


@router.post(
    "/submit",
    response_model=HumanInLoopResponse,
)
async def submit_human_review(
    request: HumanInLoopRequest,
    db: AsyncSession = Depends(get_db),
):
    service = HumanInLoopService(db)
    return await service.submit_review(request)
