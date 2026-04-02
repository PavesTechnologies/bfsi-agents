"""add underwriting monitoring snapshots

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-01 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "underwriting_monitoring_snapshots",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("segment_key", sa.String(length=100), nullable=False),
        sa.Column("generated_by", sa.String(length=100), nullable=True),
        sa.Column("thresholds", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("report", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("alerts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("baseline_records", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("current_records", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_underwriting_monitoring_snapshots_segment_key"),
        "underwriting_monitoring_snapshots",
        ["segment_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_underwriting_monitoring_snapshots_segment_key"),
        table_name="underwriting_monitoring_snapshots",
    )
    op.drop_table("underwriting_monitoring_snapshots")
