"""add decline disclosure fields

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-01 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "underwriting_decisions",
        sa.Column("adverse_action_notice", sa.Text(), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("reasoning_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("key_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("underwriting_decisions", "key_factors")
    op.drop_column("underwriting_decisions", "reasoning_summary")
    op.drop_column("underwriting_decisions", "adverse_action_notice")
