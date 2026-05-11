import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_current_user, require_permission
from src.core.permissions import Permission, Role
from src.schemas.rule import (
    ApprovalActionRequest,
    PendingApprovalOut,
    RuleCategoryOut,
    RuleCreateRequest,
    RuleDeleteRequest,
    RuleHistoryOut,
    RuleListResponse,
    RuleOut,
    RulePatchRequest,
)
from src.services.rule_service import RuleService
from src.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["Rules"])

_viewer = require_permission(Permission.VIEW_RULES)
_approver = require_permission(Permission.APPROVE_RULE_CHANGES)


@router.get("/", response_model=RuleListResponse)
async def list_rules(
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await RuleService(db).list_rules()


@router.get("/categories", response_model=list[RuleCategoryOut])
async def list_categories(
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await RuleService(db).list_categories()


@router.get("/pending-approvals", response_model=list[PendingApprovalOut])
async def pending_approvals(
    current_user: dict = Depends(_approver),
    db: AsyncSession = Depends(get_db),
):
    return await RuleService(db).get_pending_approvals()


@router.post("/", response_model=RuleHistoryOut, status_code=201)
async def create_rule(
    payload: RuleCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new rule. The rule is inserted with `is_active=False` and a
    PENDING history row — the rules_loader filters by `is_active=true`, so the
    decisioning agent only picks the rule up after a SUPER_ADMIN approves it
    via /pending-approvals/{history_id}/approve. Auto-approve path activates
    immediately when `requires_approval=false`.
    """
    role = Role(current_user["role"])
    if role not in (Role.SUPER_ADMIN, Role.CREDIT_MANAGER):
        raise HTTPException(status_code=403, detail="Permission denied")

    service = RuleService(db)
    history = await service.create_rule(payload, current_user["user_id"], role)
    await AuditService(db).log(
        "RULE_CREATE_PROPOSED",
        user_id=current_user["user_id"],
        resource_type="bank_rule",
        resource_id=str(history.rule_id),
        after={
            "rule_key": payload.rule_key,
            "category_id": payload.category_id,
            "value": payload.current_value,
            "risk_level": payload.risk_level,
            "requires_approval": payload.requires_approval,
            "approval_status": history.approval_status,
            "reason": payload.change_reason,
        },
    )
    return history


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
    logger.info("PATCH /rules/%s by user=%s payload=%r", rule_id, current_user.get("user_id"), payload.model_dump())
    try:
        role = Role(current_user["role"])
        if role not in (Role.SUPER_ADMIN, Role.CREDIT_MANAGER):
            raise HTTPException(status_code=403, detail="Permission denied")

        service = RuleService(db)
        before = await service.get_rule(rule_id)
        history = await service.propose_change(
            rule_id, payload.new_value, payload.change_reason, current_user["user_id"], role
        )
        await AuditService(db).log(
            "RULE_CHANGE_PROPOSED",
            user_id=current_user["user_id"],
            resource_type="bank_rule",
            resource_id=rule_id,
            before=before.model_dump(mode="json"),
            after={"new_value": payload.new_value, "reason": payload.change_reason},
        )
        return history
    except HTTPException:
        raise
    except Exception:
        logger.exception("PATCH /rules/%s failed", rule_id)
        raise HTTPException(status_code=500, detail="Internal error while proposing rule change — see server logs")


_APPROVE_EVENT = {
    "CREATE": "RULE_CREATE_APPROVED",
    "UPDATE": "RULE_CHANGE_APPROVED",
    "DELETE": "RULE_DELETE_APPROVED",
}
_REJECT_EVENT = {
    "CREATE": "RULE_CREATE_REJECTED",
    "UPDATE": "RULE_CHANGE_REJECTED",
    "DELETE": "RULE_DELETE_REJECTED",
}


@router.post("/pending-approvals/{history_id}/approve", response_model=RuleHistoryOut)
async def approve_rule_change(
    history_id: str,
    payload: ApprovalActionRequest,
    current_user: dict = Depends(_approver),
    db: AsyncSession = Depends(get_db),
):
    service = RuleService(db)
    result = await service.approve_change(history_id, current_user["user_id"], payload.comment)
    await AuditService(db).log(
        _APPROVE_EVENT.get(result.action_type, "RULE_CHANGE_APPROVED"),
        user_id=current_user["user_id"],
        resource_type="rule_history",
        resource_id=history_id,
        after={
            "status": "APPROVED",
            "comment": payload.comment,
            "rule_id": str(result.rule_id),
            "version": result.version,
            "action_type": result.action_type,
        },
    )
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
    await AuditService(db).log(
        _REJECT_EVENT.get(result.action_type, "RULE_CHANGE_REJECTED"),
        user_id=current_user["user_id"],
        resource_type="rule_history",
        resource_id=history_id,
        after={
            "status": "REJECTED",
            "comment": payload.comment,
            "rule_id": str(result.rule_id),
            "action_type": result.action_type,
        },
    )
    return result


@router.post("/{rule_id}/propose-delete", response_model=RuleHistoryOut)
async def propose_rule_delete(
    rule_id: str,
    payload: RuleDeleteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queues a deletion for SUPER_ADMIN review. On approve, rule.is_active
    is set to False (soft delete). On reject, rule stays active."""
    role = Role(current_user["role"])
    if role not in (Role.SUPER_ADMIN, Role.CREDIT_MANAGER):
        raise HTTPException(status_code=403, detail="Permission denied")
    service = RuleService(db)
    history = await service.propose_delete(rule_id, payload.change_reason, current_user["user_id"], role)
    await AuditService(db).log(
        "RULE_DELETE_PROPOSED",
        user_id=current_user["user_id"],
        resource_type="bank_rule",
        resource_id=rule_id,
        after={"reason": payload.change_reason, "history_id": str(history.id)},
    )
    return history


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
