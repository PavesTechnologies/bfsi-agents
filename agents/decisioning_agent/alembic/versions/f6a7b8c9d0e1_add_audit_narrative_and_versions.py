"""add audit narrative and version fields

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "underwriting_decisions",
        sa.Column("policy_version", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("model_version", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("prompt_version", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("audit_narrative", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("underwriting_decisions", "audit_narrative")
    op.drop_column("underwriting_decisions", "prompt_version")
    op.drop_column("underwriting_decisions", "model_version")
    op.drop_column("underwriting_decisions", "policy_version")
