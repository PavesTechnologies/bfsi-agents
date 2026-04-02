"""add explanation persistence fields

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-04-02 11:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "underwriting_decisions",
        sa.Column("candidate_reason_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("selected_reason_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("policy_citations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("retrieval_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("feature_attribution_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("explanation_generation_mode", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("critic_failures", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("underwriting_decisions", "critic_failures")
    op.drop_column("underwriting_decisions", "explanation_generation_mode")
    op.drop_column("underwriting_decisions", "feature_attribution_summary")
    op.drop_column("underwriting_decisions", "retrieval_evidence")
    op.drop_column("underwriting_decisions", "policy_citations")
    op.drop_column("underwriting_decisions", "selected_reason_codes")
    op.drop_column("underwriting_decisions", "candidate_reason_codes")
