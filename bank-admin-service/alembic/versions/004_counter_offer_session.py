"""counter offer session and edit audit log

Revision ID: 004_counter_offer_session
Revises: 003_decisioning_rules
Create Date: 2026-05-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_counter_offer_session"
down_revision: Union[str, None] = "003_decisioning_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── counter_offer_sessions ────────────────────────────────────────────────
    # One row per decisioning run that resulted in COUNTER_OFFER.
    # generated_options is immutable (LLM output as-is).
    # current_options is mutable (includes bank edits and bank-added options).
    op.create_table(
        "counter_offer_sessions",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("loan_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # ── Financial summary (mirrors CounterOfferMetrics in decision_state) ──
        sa.Column("original_request_dti", sa.Numeric(6, 4), nullable=False),
        sa.Column("max_affordable_emi", sa.Numeric(15, 2), nullable=False),
        sa.Column("monthly_income", sa.Numeric(15, 2), nullable=False),
        sa.Column("existing_monthly_obligations", sa.Numeric(15, 2), nullable=False),
        sa.Column("qualifying_cap", sa.Numeric(15, 2), nullable=False),

        # ── LLM-generated text ─────────────────────────────────────────────────
        sa.Column("counter_offer_logic", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=False),

        # ── Offer snapshots ────────────────────────────────────────────────────
        # generated_options: written once when decisioning agent returns;
        #   never updated — preserved as the LLM's original output.
        # current_options: starts as a copy of generated_options;
        #   updated on every bank edit or bank-added offer.
        sa.Column("generated_options", postgresql.JSONB(), nullable=False),
        sa.Column("current_options", postgresql.JSONB(), nullable=False),

        # ── Recommendation ─────────────────────────────────────────────────────
        sa.Column("recommended_option_id", sa.String(20), nullable=False),
        sa.Column("recommendation_rationale", sa.Text(), nullable=False),

        # ── Lifecycle status ───────────────────────────────────────────────────
        # DRAFT          → bank is reviewing / editing offers (not yet visible to applicant)
        # PUBLISHED      → bank published; applicant can now view and choose
        # APPLICANT_RESPONDED → applicant accepted or declined
        # EXPIRED        → expires_at passed before applicant responded
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),

        # ── Bank publish tracking ──────────────────────────────────────────────
        sa.Column(
            "published_by",
            sa.Uuid(),
            sa.ForeignKey("bank_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),

        # ── Applicant response ─────────────────────────────────────────────────
        # applicant_decision: ACCEPTED | DECLINED
        sa.Column("applicant_decision", sa.String(20), nullable=True),
        # accepted_option_id: CO1 | CO2 | CO3 | custom-<uuid>
        sa.Column("accepted_option_id", sa.String(50), nullable=True),
        sa.Column("applicant_responded_at", sa.DateTime(timezone=True), nullable=True),

        # ── Expiry ─────────────────────────────────────────────────────────────
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),

        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_counter_offer_sessions_application_id", "counter_offer_sessions", ["application_id"])
    op.create_index("ix_counter_offer_sessions_status", "counter_offer_sessions", ["status"])
    op.create_index("ix_counter_offer_sessions_expires_at", "counter_offer_sessions", ["expires_at"])

    # ── counter_offer_edit_logs ───────────────────────────────────────────────
    # Append-only audit trail. One row per field change made by a bank employee.
    # old_value / new_value are JSONB so they can hold any scalar or object.
    op.create_table(
        "counter_offer_edit_logs",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("counter_offer_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # option_id: CO1 | CO2 | CO3 | custom-<uuid>; NULL means a session-level field
        sa.Column("option_id", sa.String(50), nullable=True),
        # field_name: proposed_amount | proposed_tenure_months | proposed_interest_rate |
        #             recommended_option_id | etc.
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("old_value", postgresql.JSONB(), nullable=False),
        sa.Column("new_value", postgresql.JSONB(), nullable=False),
        sa.Column(
            "edited_by",
            sa.Uuid(),
            sa.ForeignKey("bank_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),

        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_counter_offer_edit_logs_session_id", "counter_offer_edit_logs", ["session_id"])
    op.create_index("ix_counter_offer_edit_logs_edited_at", "counter_offer_edit_logs", ["edited_at"])


def downgrade() -> None:
    op.drop_index("ix_counter_offer_edit_logs_edited_at", table_name="counter_offer_edit_logs")
    op.drop_index("ix_counter_offer_edit_logs_session_id", table_name="counter_offer_edit_logs")
    op.drop_table("counter_offer_edit_logs")

    op.drop_index("ix_counter_offer_sessions_expires_at", table_name="counter_offer_sessions")
    op.drop_index("ix_counter_offer_sessions_status", table_name="counter_offer_sessions")
    op.drop_index("ix_counter_offer_sessions_application_id", table_name="counter_offer_sessions")
    op.drop_table("counter_offer_sessions")
