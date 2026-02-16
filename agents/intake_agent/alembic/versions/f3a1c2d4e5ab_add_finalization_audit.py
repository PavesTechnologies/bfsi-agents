"""add finalization audit

Revision ID: f3a1c2d4e5ab
Revises: aaea6f1ffe54
Create Date: 2026-02-12 12:34:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f3a1c2d4e5ab"
down_revision: Union[str, Sequence[str], None] = "aaea6f1ffe54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "loan_application",
        sa.Column(
            "finalized_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Remove server-side default after backfilling existing rows
    op.alter_column("loan_application", "finalized_flag", server_default=None)

    op.create_table(
        "loan_finalization_event",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "response_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "callback_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="loan_finalization_event_pkey"),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_application.application_id"],
            name="fk_finalization_event_application",
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("loan_finalization_event")
    op.drop_column("loan_application", "finalized_flag")

