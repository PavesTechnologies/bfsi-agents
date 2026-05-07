from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, require_permission
from src.core.permissions import Permission
from src.schemas.user_rule import UserRuleOverrideCreate, UserRuleOverrideOut, UserRuleWithOverride
from src.services.audit_service import AuditService
from src.services.user_rule_service import UserRuleService

router = APIRouter(prefix="/users", tags=["User Rules"])

_viewer = require_permission(Permission.VIEW_RULES)
_manager = require_permission(Permission.MANAGE_USER_RULES)


@router.get("/{user_id}/rules", response_model=list[UserRuleWithOverride])
async def list_user_rules(
    user_id: str,
    current_user: dict = Depends(_viewer),
    db: AsyncSession = Depends(get_db),
):
    return await UserRuleService(db).list_rules_for_user(user_id)


@router.post("/{user_id}/rules/{rule_id}/override", response_model=UserRuleOverrideOut)
async def upsert_user_rule_override(
    user_id: str,
    rule_id: str,
    payload: UserRuleOverrideCreate,
    current_user: dict = Depends(_manager),
    db: AsyncSession = Depends(get_db),
):
    override = await UserRuleService(db).upsert_override(
        user_id, rule_id, payload, current_user["user_id"]
    )
    await AuditService(db).log(
        "USER_RULE_OVERRIDE_UPSERTED",
        user_id=current_user["user_id"],
        resource_type="user_rule_override",
        resource_id=str(override.id),
        after={
            "target_user_id": user_id,
            "rule_id": rule_id,
            "override_value": payload.override_value,
        },
    )
    return override


@router.delete("/{user_id}/rules/{rule_id}/override", status_code=204)
async def delete_user_rule_override(
    user_id: str,
    rule_id: str,
    current_user: dict = Depends(_manager),
    db: AsyncSession = Depends(get_db),
):
    await UserRuleService(db).delete_override(user_id, rule_id)
    await AuditService(db).log(
        "USER_RULE_OVERRIDE_DELETED",
        user_id=current_user["user_id"],
        resource_type="user_rule_override",
        resource_id=f"{user_id}:{rule_id}",
        after={"target_user_id": user_id, "rule_id": rule_id},
    )
