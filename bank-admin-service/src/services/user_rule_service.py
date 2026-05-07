import uuid
from typing import List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.bank_rule import BankRule, UserRuleOverride
from src.schemas.user_rule import UserRuleOverrideCreate, UserRuleWithOverride, UserRuleOverrideOut


class UserRuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_rules_for_user(self, user_id: str) -> List[UserRuleWithOverride]:
        """Return all active rules merged with per-user overrides via a single outer-join query."""
        uid = uuid.UUID(user_id)

        rows = (
            await self.db.execute(
                select(BankRule, UserRuleOverride)
                .outerjoin(
                    UserRuleOverride,
                    (UserRuleOverride.rule_id == BankRule.id)
                    & (UserRuleOverride.user_id == uid),
                )
                .where(BankRule.is_active == True)
                .options(selectinload(BankRule.category))
            )
        ).all()

        result = []
        for rule, override in rows:
            result.append(
                UserRuleWithOverride(
                    id=rule.id,
                    category=rule.category,
                    rule_key=rule.rule_key,
                    display_name=rule.display_name,
                    description=rule.description,
                    current_value=rule.current_value,
                    default_value=rule.default_value,
                    data_type=rule.data_type,
                    validation_schema=rule.validation_schema,
                    risk_level=rule.risk_level,
                    requires_approval=rule.requires_approval,
                    is_active=rule.is_active,
                    version=rule.version,
                    updated_at=rule.updated_at,
                    is_overridden=override is not None,
                    override_value=override.override_value if override else None,
                    override_reason=override.override_reason if override else None,
                    effective_value=override.override_value if override else rule.current_value,
                )
            )
        return result

    async def upsert_override(
        self,
        user_id: str,
        rule_id: str,
        payload: UserRuleOverrideCreate,
        created_by: str,
    ) -> UserRuleOverride:
        existing = (
            await self.db.execute(
                select(UserRuleOverride).where(
                    UserRuleOverride.user_id == uuid.UUID(user_id),
                    UserRuleOverride.rule_id == uuid.UUID(rule_id),
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.override_value = payload.override_value
            existing.override_reason = payload.override_reason
            await self.db.flush()
            return existing

        override = UserRuleOverride(
            user_id=uuid.UUID(user_id),
            rule_id=uuid.UUID(rule_id),
            override_value=payload.override_value,
            override_reason=payload.override_reason,
            created_by=uuid.UUID(created_by),
        )
        self.db.add(override)
        await self.db.flush()
        await self.db.refresh(override)  # needed for server-generated id/created_at
        return override

    async def delete_override(self, user_id: str, rule_id: str) -> None:
        result = (
            await self.db.execute(
                select(UserRuleOverride).where(
                    UserRuleOverride.user_id == uuid.UUID(user_id),
                    UserRuleOverride.rule_id == uuid.UUID(rule_id),
                )
            )
        ).scalar_one_or_none()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No override found for user {user_id} rule {rule_id}",
            )
        await self.db.delete(result)
        await self.db.flush()
