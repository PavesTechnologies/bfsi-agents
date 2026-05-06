import uuid
import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from src.models.bank_rule import BankRule, BankRuleHistory, RuleCategory
from src.models.bank_user import BankUser
from src.schemas.rule import RuleOut, RuleListResponse, RuleHistoryOut, PendingApprovalOut
from src.core.permissions import Role, has_permission, Permission


class RuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_rules(self) -> RuleListResponse:
        result = await self.db.execute(
            select(BankRule).order_by(BankRule.category_id, BankRule.rule_key)
        )
        rules = result.scalars().all()
        return RuleListResponse(items=[RuleOut.model_validate(r) for r in rules], total=len(rules))

    async def get_rule(self, rule_id: str) -> RuleOut:
        result = await self.db.execute(select(BankRule).where(BankRule.id == uuid.UUID(rule_id)))
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return RuleOut.model_validate(rule)

    async def get_rule_history(self, rule_id: str) -> list[RuleHistoryOut]:
        result = await self.db.execute(
            select(BankRuleHistory)
            .where(BankRuleHistory.rule_id == uuid.UUID(rule_id))
            .order_by(BankRuleHistory.created_at.desc())
        )
        history = result.scalars().all()
        out = []
        for h in history:
            user_result = await self.db.execute(select(BankUser).where(BankUser.id == h.changed_by))
            user = user_result.scalar_one_or_none()
            item = RuleHistoryOut.model_validate(h)
            item.changed_by_name = user.full_name or user.email if user else None
            out.append(item)
        return out

    async def propose_change(self, rule_id: str, new_value: dict, change_reason: str, user_id: str, role: Role) -> RuleHistoryOut:
        result = await self.db.execute(select(BankRule).where(BankRule.id == uuid.UUID(rule_id)))
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        # Permission check: high-risk rules require EDIT_HIGH_RISK_RULES
        if rule.risk_level == "high" and not has_permission(role, Permission.EDIT_HIGH_RISK_RULES):
            raise HTTPException(status_code=403, detail="High-risk rules require elevated permission")
        if rule.risk_level == "low" and not has_permission(role, Permission.EDIT_LOW_RISK_RULES):
            raise HTTPException(status_code=403, detail="Insufficient permission to edit rules")

        # Validate new_value against validation_schema if present
        if rule.validation_schema and "value" in new_value:
            schema = rule.validation_schema
            val = new_value["value"]
            if "min" in schema and val < schema["min"]:
                raise HTTPException(status_code=422, detail=f"Value must be >= {schema['min']}")
            if "max" in schema and val > schema["max"]:
                raise HTTPException(status_code=422, detail=f"Value must be <= {schema['max']}")

        history = BankRuleHistory(
            rule_id=rule.id,
            version=rule.version + 1,
            old_value=rule.current_value,
            new_value=new_value,
            changed_by=uuid.UUID(user_id),
            change_reason=change_reason,
            approval_status="PENDING" if rule.requires_approval else "AUTO_APPROVED",
        )
        self.db.add(history)

        # Auto-approve if rule doesn't require manual approval
        if not rule.requires_approval:
            rule.current_value = new_value
            rule.version = rule.version + 1
            rule.updated_at = datetime.datetime.now(datetime.timezone.utc)
            history.approval_status = "AUTO_APPROVED"
            history.effective_from = datetime.datetime.now(datetime.timezone.utc)

        await self.db.flush()
        await self.db.refresh(history)
        return RuleHistoryOut.model_validate(history)

    async def get_pending_approvals(self) -> list[PendingApprovalOut]:
        result = await self.db.execute(
            select(BankRuleHistory)
            .where(BankRuleHistory.approval_status == "PENDING")
            .order_by(BankRuleHistory.created_at.asc())
        )
        pending = result.scalars().all()
        out = []
        for h in pending:
            rule_result = await self.db.execute(select(BankRule).where(BankRule.id == h.rule_id))
            rule = rule_result.scalar_one_or_none()
            user_result = await self.db.execute(select(BankUser).where(BankUser.id == h.changed_by))
            user = user_result.scalar_one_or_none()
            out.append(PendingApprovalOut(
                id=h.id,
                rule_id=h.rule_id,
                rule_key=rule.rule_key if rule else "",
                rule_display_name=rule.display_name if rule else "",
                old_value=h.old_value,
                new_value=h.new_value,
                changed_by=h.changed_by,
                changed_by_name=user.full_name or user.email if user else None,
                change_reason=h.change_reason,
                created_at=h.created_at,
            ))
        return out

    async def approve_change(self, history_id: str, approver_id: str, comment: Optional[str]) -> RuleHistoryOut:
        result = await self.db.execute(select(BankRuleHistory).where(BankRuleHistory.id == uuid.UUID(history_id)))
        history = result.scalar_one_or_none()
        if not history:
            raise HTTPException(status_code=404, detail="Pending change not found")
        if history.approval_status != "PENDING":
            raise HTTPException(status_code=409, detail="Change is not in PENDING state")

        rule_result = await self.db.execute(select(BankRule).where(BankRule.id == history.rule_id))
        rule = rule_result.scalar_one_or_none()

        history.approval_status = "APPROVED"
        history.approved_by = uuid.UUID(approver_id)
        history.reviewer_comment = comment
        history.reviewed_at = datetime.datetime.now(datetime.timezone.utc)
        history.effective_from = datetime.datetime.now(datetime.timezone.utc)

        rule.current_value = history.new_value
        rule.version = history.version
        rule.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.db.flush()
        return RuleHistoryOut.model_validate(history)

    async def reject_change(self, history_id: str, approver_id: str, comment: Optional[str]) -> RuleHistoryOut:
        result = await self.db.execute(select(BankRuleHistory).where(BankRuleHistory.id == uuid.UUID(history_id)))
        history = result.scalar_one_or_none()
        if not history:
            raise HTTPException(status_code=404, detail="Pending change not found")
        if history.approval_status != "PENDING":
            raise HTTPException(status_code=409, detail="Change is not in PENDING state")

        history.approval_status = "REJECTED"
        history.approved_by = uuid.UUID(approver_id)
        history.reviewer_comment = comment
        history.reviewed_at = datetime.datetime.now(datetime.timezone.utc)

        await self.db.flush()
        return RuleHistoryOut.model_validate(history)

    async def reset_to_default(self, rule_id: str, user_id: str) -> RuleOut:
        result = await self.db.execute(select(BankRule).where(BankRule.id == uuid.UUID(rule_id)))
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        history = BankRuleHistory(
            rule_id=rule.id,
            version=rule.version + 1,
            old_value=rule.current_value,
            new_value=rule.default_value,
            changed_by=uuid.UUID(user_id),
            change_reason="Reset to default value",
            approval_status="AUTO_APPROVED",
            effective_from=datetime.datetime.now(datetime.timezone.utc),
        )
        self.db.add(history)
        rule.current_value = rule.default_value
        rule.version = rule.version + 1
        rule.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.db.flush()
        return RuleOut.model_validate(rule)

    async def get_active_rules_dict(self) -> dict:
        """Returns all active rules as a flat dict {rule_key: value} — consumed by the decisioning agent."""
        result = await self.db.execute(select(BankRule).where(BankRule.is_active == True))
        rules = result.scalars().all()
        return {r.rule_key: r.current_value.get("value") for r in rules}
