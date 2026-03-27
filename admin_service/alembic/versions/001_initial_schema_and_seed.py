"""Initial schema: lender_users, human_review_queue, human_review_decisions,
risk_tier_config, loan_policies. Seeds default ADMIN user and config data.

Revision ID: 001
Revises:
Create Date: 2026-03-26
"""

from typing import Sequence, Union
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # lender_users
    # ------------------------------------------------------------------
    op.create_table(
        "lender_users",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_lender_users_email", "lender_users", ["email"])

    # ------------------------------------------------------------------
    # human_review_queue
    # ------------------------------------------------------------------
    op.create_table(
        "human_review_queue",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("application_id", sa.String(255), unique=True, nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="PENDING"
        ),
        sa.Column(
            "assigned_to",
            UUID(as_uuid=True),
            sa.ForeignKey("lender_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ai_decision", sa.String(20), nullable=False),
        sa.Column("ai_risk_tier", sa.String(5), nullable=True),
        sa.Column("ai_risk_score", sa.Float, nullable=True),
        sa.Column("ai_suggested_amount", sa.Float, nullable=True),
        sa.Column("ai_suggested_rate", sa.Float, nullable=True),
        sa.Column("ai_suggested_tenure", sa.Integer, nullable=True),
        sa.Column("ai_counter_options", JSONB, nullable=True),
        sa.Column("ai_reasoning", JSONB, nullable=True),
        sa.Column("ai_decline_reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_human_review_queue_application_id", "human_review_queue", ["application_id"]
    )
    op.create_index("ix_human_review_queue_status", "human_review_queue", ["status"])

    # ------------------------------------------------------------------
    # human_review_decisions
    # ------------------------------------------------------------------
    op.create_table(
        "human_review_decisions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "queue_id",
            UUID(as_uuid=True),
            sa.ForeignKey("human_review_queue.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("application_id", sa.String(255), nullable=False),
        sa.Column(
            "reviewed_by",
            UUID(as_uuid=True),
            sa.ForeignKey("lender_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("override_amount", sa.Float, nullable=True),
        sa.Column("override_rate", sa.Float, nullable=True),
        sa.Column("override_tenure", sa.Integer, nullable=True),
        sa.Column("selected_offer_id", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_human_review_decisions_application_id",
        "human_review_decisions",
        ["application_id"],
    )

    # ------------------------------------------------------------------
    # risk_tier_config
    # ------------------------------------------------------------------
    op.create_table(
        "risk_tier_config",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tier", sa.String(5), nullable=False),
        sa.Column("min_interest_rate", sa.Float, nullable=False),
        sa.Column("max_interest_rate", sa.Float, nullable=False),
        sa.Column("default_interest_rate", sa.Float, nullable=False),
        sa.Column("max_loan_amount", sa.Float, nullable=False),
        sa.Column("min_loan_amount", sa.Float, nullable=False),
        sa.Column("min_credit_score", sa.Integer, nullable=False),
        sa.Column("max_dti_ratio", sa.Float, nullable=False),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default="true"
        ),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("lender_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("ix_risk_tier_config_tier", "risk_tier_config", ["tier"])

    # ------------------------------------------------------------------
    # loan_policies
    # ------------------------------------------------------------------
    op.create_table(
        "loan_policies",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("policy_key", sa.String(100), nullable=False),
        sa.Column("policy_value", JSONB, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default="true"
        ),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("lender_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("ix_loan_policies_policy_key", "loan_policies", ["policy_key"])

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------
    _seed_data()


def _seed_data() -> None:
    import bcrypt

    bind = op.get_bind()
    now = datetime.now(timezone.utc)

    # Seed default ADMIN user
    admin_id = "00000000-0000-0000-0000-000000000001"
    password_hash = bcrypt.hashpw(b"changeme", bcrypt.gensalt()).decode()
    bind.execute(
        sa.text(
            """
            INSERT INTO lender_users (id, email, password_hash, full_name, role, is_active, created_at, updated_at)
            VALUES (:id, :email, :password_hash, :full_name, :role, true, :now, :now)
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {
            "id": admin_id,
            "email": "admin@bank.com",
            "password_hash": password_hash,
            "full_name": "System Administrator",
            "role": "ADMIN",
            "now": now,
        },
    )

    # Seed risk tier configs
    tiers = [
        ("A", 6.0, 10.0, 7.5, 500000.0, 10000.0, 750, 0.35),
        ("B", 9.0, 14.0, 11.0, 200000.0, 5000.0, 650, 0.43),
        ("C", 14.0, 20.0, 16.5, 75000.0, 1000.0, 580, 0.50),
        ("F", 20.0, 28.0, 24.0, 25000.0, 500.0, 500, 0.55),
    ]
    for tier, min_r, max_r, def_r, max_loan, min_loan, min_score, max_dti in tiers:
        bind.execute(
            sa.text(
                """
                INSERT INTO risk_tier_config
                    (tier, min_interest_rate, max_interest_rate, default_interest_rate,
                     max_loan_amount, min_loan_amount, min_credit_score, max_dti_ratio,
                     is_active, effective_from, created_by, notes)
                VALUES
                    (:tier, :min_r, :max_r, :def_r, :max_loan, :min_loan, :min_score,
                     :max_dti, true, :now, :admin_id, 'Initial seed data')
                """
            ),
            {
                "tier": tier,
                "min_r": min_r,
                "max_r": max_r,
                "def_r": def_r,
                "max_loan": max_loan,
                "min_loan": min_loan,
                "min_score": min_score,
                "max_dti": max_dti,
                "now": now,
                "admin_id": admin_id,
            },
        )

    # Seed loan policies
    policies = [
        (
            "AUTO_APPROVE_BELOW_AMOUNT",
            {"value": 10000, "unit": "USD"},
            "Automatically approve applications below this loan amount without human review",
            "UNDERWRITING",
        ),
        (
            "REQUIRE_HUMAN_REVIEW_ABOVE_AMOUNT",
            {"value": 75000, "unit": "USD"},
            "Always require human review for loans above this amount",
            "UNDERWRITING",
        ),
        (
            "MAX_LOAN_PERSONAL",
            {"value": 500000, "unit": "USD"},
            "Maximum allowed personal loan amount",
            "LIMITS",
        ),
        (
            "MIN_INCOME_MONTHLY",
            {"value": 2000, "unit": "USD"},
            "Minimum monthly income required for any loan application",
            "UNDERWRITING",
        ),
        (
            "ORIGINATION_FEE_PERCENT",
            {"value": 2.0, "unit": "percent"},
            "Loan origination fee as a percentage of approved loan amount",
            "DISBURSEMENT",
        ),
        (
            "KYC_CONFIDENCE_THRESHOLD",
            {"value": 0.75, "unit": "score"},
            "Minimum KYC confidence score required to pass identity verification",
            "KYC",
        ),
    ]
    import json
    for key, value, description, category in policies:
        bind.execute(
            sa.text(
                """
                INSERT INTO loan_policies
                    (policy_key, policy_value, description, category,
                     is_active, effective_from, created_by, notes)
                VALUES
                    (:key, CAST(:value AS jsonb), :description, :category,
                     true, :now, :admin_id, 'Initial seed data')
                """
            ),
            {
                "key": key,
                "value": json.dumps(value),
                "description": description,
                "category": category,
                "now": now,
                "admin_id": admin_id,
            },
        )


def downgrade() -> None:
    op.drop_table("loan_policies")
    op.drop_table("risk_tier_config")
    op.drop_table("human_review_decisions")
    op.drop_table("human_review_queue")
    op.drop_table("lender_users")
