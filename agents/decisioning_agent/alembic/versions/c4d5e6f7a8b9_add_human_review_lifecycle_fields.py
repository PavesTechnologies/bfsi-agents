"""add human review lifecycle fields

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-04-02 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "underwriting_decisions",
        sa.Column("human_review_required", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("human_review_status", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("human_review_outcome", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "underwriting_decisions",
        sa.Column("latest_human_review_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "underwriting_human_reviews",
        sa.Column("underwriting_decision_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "underwriting_human_reviews",
        sa.Column("review_status", sa.String(length=50), nullable=False, server_default="REVIEW_COMPLETED"),
    )
    op.create_index(
        op.f("ix_underwriting_human_reviews_underwriting_decision_id"),
        "underwriting_human_reviews",
        ["underwriting_decision_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_underwriting_human_reviews_underwriting_decision_id"),
        table_name="underwriting_human_reviews",
    )
    op.drop_column("underwriting_human_reviews", "review_status")
    op.drop_column("underwriting_human_reviews", "underwriting_decision_id")
    op.drop_column("underwriting_decisions", "latest_human_review_id")
    op.drop_column("underwriting_decisions", "human_review_outcome")
    op.drop_column("underwriting_decisions", "human_review_status")
    op.drop_column("underwriting_decisions", "human_review_required")
