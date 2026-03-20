"""add transition log table

Revision ID: 7d3e5ab12c44
Revises: 2c1e8d7b4f90
Create Date: 2026-03-11 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7d3e5ab12c44"
down_revision: Union[str, Sequence[str], None] = "2c1e8d7b4f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "disbursement_transition_logs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.String(length=50), nullable=False),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "transition_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_disbursement_transition_logs_application_id"),
        "disbursement_transition_logs",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_disbursement_transition_logs_correlation_id"),
        "disbursement_transition_logs",
        ["correlation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_disbursement_transition_logs_correlation_id"),
        table_name="disbursement_transition_logs",
    )
    op.drop_index(
        op.f("ix_disbursement_transition_logs_application_id"),
        table_name="disbursement_transition_logs",
    )
    op.drop_table("disbursement_transition_logs")
