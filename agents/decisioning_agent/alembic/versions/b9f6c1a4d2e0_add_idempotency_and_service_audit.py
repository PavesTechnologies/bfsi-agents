"""add idempotency and service audit

Revision ID: b9f6c1a4d2e0
Revises: a70c9a5e17ba
Create Date: 2026-03-11 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b9f6c1a4d2e0"
down_revision: Union[str, Sequence[str], None] = "a70c9a5e17ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "underwriting_decisions",
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        op.f("ix_underwriting_decisions_correlation_id"),
        "underwriting_decisions",
        ["correlation_id"],
        unique=False,
    )

    op.create_table(
        "underwriting_idempotency",
        sa.Column("application_id", sa.String(length=50), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("application_id"),
    )

    op.create_table(
        "service_audit_logs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.String(length=50), nullable=False),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
        sa.Column("agent_name", sa.String(length=50), nullable=False),
        sa.Column("operation_name", sa.String(length=100), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_audit_logs_application_id"),
        "service_audit_logs",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_service_audit_logs_correlation_id"),
        "service_audit_logs",
        ["correlation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_service_audit_logs_correlation_id"), table_name="service_audit_logs")
    op.drop_index(op.f("ix_service_audit_logs_application_id"), table_name="service_audit_logs")
    op.drop_table("service_audit_logs")
    op.drop_table("underwriting_idempotency")
    op.drop_index(
        op.f("ix_underwriting_decisions_correlation_id"),
        table_name="underwriting_decisions",
    )
    op.drop_column("underwriting_decisions", "correlation_id")
