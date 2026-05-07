"""HITL loan applications and user rule overrides

Revision ID: 002_hitl_and_user_rules
Revises: 001_initial_schema
Create Date: 2026-05-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_hitl_and_user_rules"
down_revision: Union[str, Sequence[str], None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- user_rule_overrides ---
    op.create_table(
        "user_rule_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("override_value", postgresql.JSONB(), nullable=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["bank_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["bank_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["bank_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "rule_id", name="uq_user_rule_override"),
    )
    op.create_index("ix_user_rule_overrides_user_id", "user_rule_overrides", ["user_id"])

    # --- loan_applications ---
    op.create_table(
        "loan_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("external_application_id", sa.String(255), nullable=False),
        sa.Column("pipeline_status", sa.String(50), server_default="RECEIVED", nullable=False),

        sa.Column("applicant_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("loan_amount_requested", sa.Numeric(15, 2), nullable=False),
        sa.Column("loan_tenure_months", sa.Integer(), nullable=False),
        sa.Column("loan_purpose", sa.String(255), nullable=True),

        sa.Column("kyc_status", sa.String(20), nullable=True),
        sa.Column("kyc_result_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("kyc_completed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("active_analyzers", postgresql.JSONB(), nullable=True),
        sa.Column("analyzers_selected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analyzers_selected_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("decisioning_result_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("llm_decision", sa.String(30), nullable=True),
        sa.Column("llm_risk_tier", sa.String(5), nullable=True),
        sa.Column("llm_risk_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("llm_approved_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("llm_interest_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("llm_tenure_months", sa.Integer(), nullable=True),
        sa.Column("llm_counter_offer_options", postgresql.JSONB(), nullable=True),
        sa.Column("decisioning_completed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("bank_final_decision", sa.String(30), nullable=True),
        sa.Column("bank_approved_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("bank_interest_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("bank_tenure_months", sa.Integer(), nullable=True),
        sa.Column("bank_override_reason", sa.Text(), nullable=True),
        sa.Column("bank_decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("bank_decided_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("applicant_accepted", sa.Boolean(), nullable=True),
        sa.Column("applicant_responded_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("loan_document_path", sa.Text(), nullable=True),
        sa.Column("loan_document_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signature_full_name", sa.String(255), nullable=True),
        sa.Column("signature_agreed", sa.Boolean(), nullable=True),
        sa.Column("signature_ip", sa.String(50), nullable=True),
        sa.Column("signature_user_agent", sa.Text(), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("disbursement_transaction_id", sa.String(255), nullable=True),
        sa.Column("disbursed_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("disbursed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disbursement_receipt_snapshot", postgresql.JSONB(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),

        sa.ForeignKeyConstraint(["analyzers_selected_by"], ["bank_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["bank_decided_by"], ["bank_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_loan_applications_external_application_id", "loan_applications", ["external_application_id"], unique=True)
    op.create_index("ix_loan_applications_pipeline_status", "loan_applications", ["pipeline_status"])


def downgrade() -> None:
    op.drop_table("loan_applications")
    op.drop_table("user_rule_overrides")
