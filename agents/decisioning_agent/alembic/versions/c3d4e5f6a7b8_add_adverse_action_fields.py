"""add adverse action fields

Revision ID: c3d4e5f6a7b8
Revises: 7a28723bdf31
Create Date: 2026-04-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "7a28723bdf31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "underwriting_decisions",
        sa.Column("primary_reason_key", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("secondary_reason_key", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("adverse_action_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("underwriting_decisions", "adverse_action_reasons")
    op.drop_column("underwriting_decisions", "secondary_reason_key")
    op.drop_column("underwriting_decisions", "primary_reason_key")
