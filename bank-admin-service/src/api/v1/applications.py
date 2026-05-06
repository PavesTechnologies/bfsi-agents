from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, require_permission
from src.core.permissions import Permission
from src.schemas.application import ApplicationListResponse, ApplicationDetail, DashboardStats, DailyVolume
from src.services.application_service import ApplicationService
from src.services.rule_service import RuleService

router = APIRouter(prefix="/applications", tags=["Applications"])

_viewer = require_permission(Permission.VIEW_APPLICATIONS)
_exporter = require_permission(Permission.EXPORT_APPLICATIONS)


@router.get("/stats/overview", response_model=DashboardStats)
async def dashboard_stats(
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    rule_service = RuleService(db)
    pending = await rule_service.get_pending_approvals()
    app_service = ApplicationService(db)
    return await app_service.get_dashboard_stats(pending_rule_approvals=len(pending))


@router.get("/stats/daily-volume", response_model=list[DailyVolume])
async def daily_volume(
    days: int = Query(14, ge=1, le=90),
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await ApplicationService(db).get_daily_volume(days)


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    decision: Optional[str] = Query(None, description="APPROVE | DECLINE | COUNTER_OFFER"),
    risk_tier: Optional[str] = Query(None, description="A | B | C | F"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await ApplicationService(db).list_applications(page, page_size, decision, risk_tier, date_from, date_to)


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(
    application_id: str,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await ApplicationService(db).get_application(application_id)
