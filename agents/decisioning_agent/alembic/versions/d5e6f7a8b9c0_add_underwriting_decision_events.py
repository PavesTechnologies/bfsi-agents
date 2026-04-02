"""add underwriting decision events

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-02 10:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "underwriting_decision_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.String(length=50), nullable=False),
        sa.Column("underwriting_decision_id", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_status", sa.String(length=50), nullable=True),
        sa.Column("actor", sa.String(length=100), nullable=True),
        sa.Column("event_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_underwriting_decision_events_application_id"),
        "underwriting_decision_events",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_underwriting_decision_events_underwriting_decision_id"),
        "underwriting_decision_events",
        ["underwriting_decision_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_underwriting_decision_events_underwriting_decision_id"),
        table_name="underwriting_decision_events",
    )
    op.drop_index(
        op.f("ix_underwriting_decision_events_application_id"),
        table_name="underwriting_decision_events",
    )
    op.drop_table("underwriting_decision_events")
