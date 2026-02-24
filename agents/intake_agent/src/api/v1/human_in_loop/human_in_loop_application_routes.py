from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.interfaces.human_in_loop_interface import GetApplicationResponse
from src.services.human_in_loop_services.human_in_loop_appli_service import (
    ApplicationGetService,
)
from src.utils.intake_database.db_session import get_db

router = APIRouter(
    prefix="/human_review/applications",
    tags=["Human In Loop"],
)


@router.get(
    "/{application_id}",
    response_model=GetApplicationResponse,
)
async def get_application_by_id(
    application_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ApplicationGetService(db)
    return await service.get_by_application_id(application_id)
