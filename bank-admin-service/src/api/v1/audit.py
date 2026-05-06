from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import datetime
import uuid

from src.core.dependencies import get_db, require_permission
from src.core.permissions import Permission
from src.models.bank_user import BankAdminAuditLog

router = APIRouter(prefix="/audit", tags=["Audit"])

_auditor = require_permission(Permission.VIEW_AUDIT_LOGS)


class AuditLogOut(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    before_snapshot: Optional[dict] = None
    after_snapshot: Optional[dict] = None
    ip_address: Optional[str] = None
    extra: Optional[dict] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[AuditLogOut])
async def list_audit_logs(
    user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(_auditor),
    db: AsyncSession = Depends(get_db),
):
    query = select(BankAdminAuditLog).order_by(BankAdminAuditLog.created_at.desc()).limit(limit)
    if user_id:
        query = query.where(BankAdminAuditLog.user_id == uuid.UUID(user_id))
    if resource_type:
        query = query.where(BankAdminAuditLog.resource_type == resource_type)
    if action:
        query = query.where(BankAdminAuditLog.action == action)

    result = await db.execute(query)
    return [AuditLogOut.model_validate(r) for r in result.scalars().all()]
