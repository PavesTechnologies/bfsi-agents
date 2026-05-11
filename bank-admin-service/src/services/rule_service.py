import logging
import uuid
import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, func
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from src.models.bank_rule import BankRule, BankRuleHistory, RuleCategory
from src.models.bank_user import BankUser
from src.schemas.rule import (
    RuleCategoryOut,
    RuleCreateRequest,
    RuleHistoryOut,
    RuleListResponse,
    RuleOut,
    PendingApprovalOut,
)
from src.core.permissions import Role, has_permission, Permission


logger = logging.getLogger(__name__)


# Sentinel payload that marks a "propose DELETE" entry in bank_rule_history.
# Stored in new_value; approve_change recognizes it and soft-deletes the rule.
_DELETE_SENTINEL = {"_delete": True}


def _classify_history(h: BankRuleHistory) -> str:
    """CREATE | UPDATE | DELETE based on history row shape."""
    if h.new_value == _DELETE_SENTINEL:
        return "DELETE"
    if h.old_value is None:
        return "CREATE"
    return "UPDATE"


def _history_out(h: BankRuleHistory, changed_by_name: Optional[str] = None) -> RuleHistoryOut:
    """Explicit construction — model_validate(h) doesn't see the new
    `action_type` field because the ORM has no such attribute. Building the
    object manually keeps the response stable."""
    return RuleHistoryOut(
        id=h.id,
        rule_id=h.rule_id,
        version=h.version,
        action_type=_classify_history(h),
        old_value=h.old_value,
        new_value=h.new_value,
        changed_by=h.changed_by,
        changed_by_name=changed_by_name,
        change_reason=h.change_reason,
        approval_status=h.approval_status,
        reviewer_comment=h.reviewer_comment,
        created_at=h.created_at,
        reviewed_at=h.reviewed_at,
    )


class RuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_rules(self) -> RuleListResponse:
        # Exclude rejected creates and soft-deleted rules. Visible:
        # - is_active = True (approved + live)
        # - is_active = False AND has at least one PENDING history row (pending CREATE)
        pending_subq = select(BankRuleHistory.rule_id).where(
            BankRuleHistory.approval_status == "PENDING"
        )
        result = await self.db.execute(
            select(BankRule)
            .options(joinedload(BankRule.category))
            .where(or_(BankRule.is_active == True, BankRule.id.in_(pending_subq)))
            .order_by(BankRule.category_id, BankRule.rule_key)
        )
        rules = result.scalars().all()
        return RuleListResponse(items=[RuleOut.model_validate(r) for r in rules], total=len(rules))

    async def list_categories(self) -> list[RuleCategoryOut]:
        result = await self.db.execute(select(RuleCategory).order_by(RuleCategory.id))
        return [RuleCategoryOut.model_validate(c) for c in result.scalars().all()]

    async def create_rule(
        self, payload: RuleCreateRequest, user_id: str, role: Role
    ) -> RuleHistoryOut:
        """Create a new rule + PENDING history row. The new BankRule is inserted
        with `is_active=False` so the decisioning agent never picks it up until
        the create is approved (which flips is_active=True).

        Auto-approve path: when `requires_approval=False` and the user has the
        right permission, we activate the rule immediately and mark the history
        row AUTO_APPROVED.
        """
        # Permissions — same gates as edit: high-risk requires elevated.
        if payload.risk_level == "high" and not has_permission(role, Permission.EDIT_HIGH_RISK_RULES):
            raise HTTPException(status_code=403, detail="High-risk rules require elevated permission")
        if payload.risk_level == "low" and not has_permission(role, Permission.EDIT_LOW_RISK_RULES):
            raise HTTPException(status_code=403, detail="Insufficient permission to create rules")

        # Category must exist.
        cat = (await self.db.execute(select(RuleCategory).where(RuleCategory.id == payload.category_id))).scalar_one_or_none()
        if not cat:
            raise HTTPException(status_code=404, detail=f"Category {payload.category_id} not found")

        # Unique rule_key.
        existing = (await self.db.execute(select(BankRule).where(BankRule.rule_key == payload.rule_key))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail=f"rule_key '{payload.rule_key}' already exists")

        # Schema-level value validation (same shape used by propose_change).
        if payload.validation_schema and isinstance(payload.current_value, dict) and "value" in payload.current_value:
            schema = payload.validation_schema
            val = payload.current_value["value"]
            if "min" in schema and isinstance(val, (int, float)) and val < schema["min"]:
                raise HTTPException(status_code=422, detail=f"Value must be >= {schema['min']}")
            if "max" in schema and isinstance(val, (int, float)) and val > schema["max"]:
                raise HTTPException(status_code=422, detail=f"Value must be <= {schema['max']}")

        now = datetime.datetime.now(datetime.timezone.utc)
        default_value = payload.default_value or payload.current_value

        # All new rules go through HITL; insert inactive and create a PENDING
        # history row. `requires_approval` on the payload is ignored — the
        # SUPER_ADMIN approves via /rules/pending-approvals/{id}/approve.
        rule = BankRule(
            category_id=payload.category_id,
            rule_key=payload.rule_key,
            display_name=payload.display_name,
            description=payload.description,
            current_value=payload.current_value,
            default_value=default_value,
            data_type=payload.data_type,
            validation_schema=payload.validation_schema,
            risk_level=payload.risk_level,
            requires_approval=True,
            is_active=False,
            version=1,
            created_at=now,
            updated_at=now,
        )
        self.db.add(rule)
        await self.db.flush()  # populate rule.id

        history = BankRuleHistory(
            rule_id=rule.id,
            version=1,
            old_value=None,  # marker: this is a CREATE
            new_value=payload.current_value,
            changed_by=uuid.UUID(user_id),
            change_reason=payload.change_reason,
            approval_status="PENDING",
        )
        self.db.add(history)

        await self.db.flush()
        await self.db.refresh(history)
        return _history_out(history)

    async def propose_delete(
        self, rule_id: str, change_reason: str, user_id: str, role: Role
    ) -> RuleHistoryOut:
        """Queue a deletion for approval. On approve the rule is soft-deleted
        (is_active=False). The bank_rule row stays for audit linkage; the
        decisioning agent stops seeing it on the next request because its
        repository filters `is_active=true`."""
        logger.info("propose_delete rule_id=%s reason=%r", rule_id, change_reason)
        result = await self.db.execute(select(BankRule).where(BankRule.id == uuid.UUID(rule_id)))
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        # Reuse the edit permission gates — high-risk deletions need elevated.
        if rule.risk_level == "high" and not has_permission(role, Permission.EDIT_HIGH_RISK_RULES):
            raise HTTPException(status_code=403, detail="High-risk rules require elevated permission")
        if rule.risk_level == "low" and not has_permission(role, Permission.EDIT_LOW_RISK_RULES):
            raise HTTPException(status_code=403, detail="Insufficient permission to delete rules")

        # Reject a second concurrent deletion proposal.
        existing = await self.db.execute(
            select(BankRuleHistory).where(
                BankRuleHistory.rule_id == rule.id,
                BankRuleHistory.approval_status == "PENDING",
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="A pending change already exists for this rule")

        history = BankRuleHistory(
            rule_id=rule.id,
            version=rule.version + 1,
            old_value=rule.current_value,
            new_value=_DELETE_SENTINEL,
            changed_by=uuid.UUID(user_id),
            change_reason=change_reason,
            approval_status="PENDING",
        )
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history)
        return _history_out(history)

    async def get_rule(self, rule_id: str) -> RuleOut:
        # joinedload(category) — RuleOut nests RuleCategoryOut, and lazy-loading
        # a relationship from an AsyncSession blows up with MissingGreenlet.
        result = await self.db.execute(
            select(BankRule)
            .options(joinedload(BankRule.category))
            .where(BankRule.id == uuid.UUID(rule_id))
        )
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
            out.append(_history_out(h, user.full_name or user.email if user else None))
        return out

    async def propose_change(self, rule_id: str, new_value: dict, change_reason: str, user_id: str, role: Role) -> RuleHistoryOut:
        logger.info("propose_change rule_id=%s new_value=%r reason=%r", rule_id, new_value, change_reason)
        try:
            result = await self.db.execute(select(BankRule).where(BankRule.id == uuid.UUID(rule_id)))
            rule = result.scalar_one_or_none()
            if not rule:
                raise HTTPException(status_code=404, detail="Rule not found")

            # Permission check: high-risk rules require EDIT_HIGH_RISK_RULES
            if rule.risk_level == "high" and not has_permission(role, Permission.EDIT_HIGH_RISK_RULES):
                raise HTTPException(status_code=403, detail="High-risk rules require elevated permission")
            if rule.risk_level == "low" and not has_permission(role, Permission.EDIT_LOW_RISK_RULES):
                raise HTTPException(status_code=403, detail="Insufficient permission to edit rules")

            # Validate new_value against validation_schema if present.
            # min/max only apply to numeric values — skip for json arrays / dicts / booleans.
            if rule.validation_schema and isinstance(new_value, dict) and "value" in new_value:
                schema = rule.validation_schema
                val = new_value["value"]
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    if "min" in schema and val < schema["min"]:
                        raise HTTPException(status_code=422, detail=f"Value must be >= {schema['min']}")
                    if "max" in schema and val > schema["max"]:
                        raise HTTPException(status_code=422, detail=f"Value must be <= {schema['max']}")

            # Every change is queued for SUPER_ADMIN review. We never mutate
            # `rule.current_value` here — that's the approver's job.
            history = BankRuleHistory(
                rule_id=rule.id,
                version=rule.version + 1,
                old_value=rule.current_value,
                new_value=new_value,
                changed_by=uuid.UUID(user_id),
                change_reason=change_reason,
                approval_status="PENDING",
            )
            self.db.add(history)

            await self.db.flush()
            await self.db.refresh(history)
            return _history_out(history)
        except HTTPException:
            raise
        except Exception:
            logger.exception("propose_change failed for rule_id=%s", rule_id)
            raise

    async def get_pending_approvals(self) -> list[PendingApprovalOut]:
        result = await self.db.execute(
            select(BankRuleHistory)
            .where(BankRuleHistory.approval_status == "PENDING")
            .order_by(BankRuleHistory.created_at.asc())
        )
        pending = result.scalars().all()
        out = []
        for h in pending:
            rule_result = await self.db.execute(
                select(BankRule).options(joinedload(BankRule.category)).where(BankRule.id == h.rule_id)
            )
            rule = rule_result.scalar_one_or_none()
            user_result = await self.db.execute(select(BankUser).where(BankUser.id == h.changed_by))
            user = user_result.scalar_one_or_none()
            action = _classify_history(h)
            out.append(PendingApprovalOut(
                id=h.id,
                rule_id=h.rule_id,
                rule_key=rule.rule_key if rule else "",
                rule_display_name=rule.display_name if rule else "",
                category_name=rule.category.name if rule and rule.category else None,
                risk_level=rule.risk_level if rule else None,
                action_type=action,
                is_create=action == "CREATE",
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

        now = datetime.datetime.now(datetime.timezone.utc)
        history.approval_status = "APPROVED"
        history.approved_by = uuid.UUID(approver_id)
        history.reviewer_comment = comment
        history.reviewed_at = now
        history.effective_from = now

        action = _classify_history(history)
        if action == "DELETE":
            # Soft delete — rules_loader's `WHERE is_active=true` filter
            # excludes the row immediately. The current_value stays as-is so
            # a future undo could restore from history.
            rule.is_active = False
            rule.updated_at = now
        elif action == "CREATE":
            rule.current_value = history.new_value
            rule.version = history.version
            rule.updated_at = now
            rule.is_active = True
        else:  # UPDATE
            rule.current_value = history.new_value
            rule.version = history.version
            rule.updated_at = now

        await self.db.flush()
        return _history_out(history)

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

        # Reject leaves the rule untouched.
        # - CREATE rejection: rule was already is_active=False from create_rule.
        #   list_rules filters it out because no PENDING history remains.
        # - UPDATE rejection: rule.current_value is unchanged.
        # - DELETE rejection: rule stays active.

        await self.db.flush()
        return _history_out(history)

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
