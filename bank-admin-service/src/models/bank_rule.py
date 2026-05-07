import uuid
import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime, Text, ForeignKey, text, Uuid, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base


class RuleCategory(Base):
    __tablename__ = "rule_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    rules: Mapped[list["BankRule"]] = relationship("BankRule", back_populates="category")


class BankRule(Base):
    __tablename__ = "bank_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("rule_categories.id"), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    default_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    validation_schema: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), server_default="low", nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    category: Mapped[RuleCategory] = relationship("RuleCategory", back_populates="rules")
    history: Mapped[list["BankRuleHistory"]] = relationship("BankRuleHistory", back_populates="rule", foreign_keys="BankRuleHistory.rule_id")


class BankRuleHistory(Base):
    __tablename__ = "bank_rule_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    rule_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bank_rules.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    old_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bank_users.id"), nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("bank_users.id", ondelete="SET NULL"), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(20), server_default="PENDING", nullable=False, index=True)
    reviewer_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    effective_from: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    rule: Mapped[BankRule] = relationship("BankRule", back_populates="history", foreign_keys=[rule_id])


class UserRuleOverride(Base):
    """Per-user rule value set by SUPER_ADMIN. Takes precedence over the global BankRule value."""
    __tablename__ = "user_rule_overrides"
    __table_args__ = (UniqueConstraint("user_id", "rule_id", name="uq_user_rule_override"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bank_users.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bank_rules.id", ondelete="CASCADE"), nullable=False)
    override_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bank_users.id"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
