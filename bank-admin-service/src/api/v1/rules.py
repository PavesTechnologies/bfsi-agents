from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_current_user, require_permission
from src.core.permissions import Permission, Role
from src.schemas.rule import RuleListResponse, RuleOut, RulePatchRequest, RuleHistoryOut, PendingApprovalOut, ApprovalActionRequest
from src.services.rule_service import RuleService
from src.services.audit_service import AuditService

router = APIRouter(prefix="/rules", tags=["Rules"])

_viewer = require_permission(Permission.VIEW_RULES)
_approver = require_permission(Permission.APPROVE_RULE_CHANGES)


@router.get("/", response_model=RuleListResponse)
async def list_rules(
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await RuleService(db).list_rules()


@router.get("/pending-approvals", response_model=list[PendingApprovalOut])
async def pending_approvals(
    current_user: dict = Depends(_approver),
    db: AsyncSession = Depends(get_db),
):
    return await RuleService(db).get_pending_approvals()


@router.get("/{rule_id}", response_model=RuleOut)
async def get_rule(
    rule_id: str,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await RuleService(db).get_rule(rule_id)


@router.get("/{rule_id}/history", response_model=list[RuleHistoryOut])
async def rule_history(
    rule_id: str,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await RuleService(db).get_rule_history(rule_id)


@router.patch("/{rule_id}", response_model=RuleHistoryOut)
async def propose_rule_change(
    rule_id: str,
    payload: RulePatchRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = Role(current_user["role"])
    # Minimum permission: must be able to edit at least low-risk rules
    if not (Permission.EDIT_LOW_RISK_RULES in (p for p in Permission) and
            role in (Role.SUPER_ADMIN, Role.CREDIT_MANAGER)):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = RuleService(db)
    before = await service.get_rule(rule_id)
    history = await service.propose_change(rule_id, payload.new_value, payload.change_reason, current_user["user_id"], role)
    await AuditService(db).log("RULE_CHANGE_PROPOSED", user_id=current_user["user_id"], resource_type="bank_rule", resource_id=rule_id, before=before.model_dump(mode="json"), after={"new_value": payload.new_value, "reason": payload.change_reason})
    return history


@router.post("/pending-approvals/{history_id}/approve", response_model=RuleHistoryOut)
async def approve_rule_change(
    history_id: str,
    payload: ApprovalActionRequest,
    current_user: dict = Depends(_approver),
    db: AsyncSession = Depends(get_db),
):
    service = RuleService(db)
    result = await service.approve_change(history_id, current_user["user_id"], payload.comment)
    await AuditService(db).log("RULE_CHANGE_APPROVED", user_id=current_user["user_id"], resource_type="rule_history", resource_id=history_id, after={"status": "APPROVED", "comment": payload.comment})
    return result


@router.post("/pending-approvals/{history_id}/reject", response_model=RuleHistoryOut)
async def reject_rule_change(
    history_id: str,
    payload: ApprovalActionRequest,
    current_user: dict = Depends(_approver),
    db: AsyncSession = Depends(get_db),
):
    service = RuleService(db)
    result = await service.reject_change(history_id, current_user["user_id"], payload.comment)
    await AuditService(db).log("RULE_CHANGE_REJECTED", user_id=current_user["user_id"], resource_type="rule_history", resource_id=history_id, after={"status": "REJECTED", "comment": payload.comment})
    return result


@router.post("/{rule_id}/reset", response_model=RuleOut)
async def reset_rule(
    rule_id: str,
    current_user: dict = Depends(_approver),
    db: AsyncSession = Depends(get_db),
):
    result = await RuleService(db).reset_to_default(rule_id, current_user["user_id"])
    await AuditService(db).log("RULE_RESET", user_id=current_user["user_id"], resource_type="bank_rule", resource_id=rule_id)
    return result


@router.get("/export/active", response_model=dict)
async def export_active_rules(
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    """Returns all active rules as a flat dict — consumed by the decisioning agent."""
    return await RuleService(db).get_active_rules_dict()
