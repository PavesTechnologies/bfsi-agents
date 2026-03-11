"""add idempotency and service audit

Revision ID: 2c1e8d7b4f90
Revises: 87465391ba17
Create Date: 2026-03-11 15:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2c1e8d7b4f90"
down_revision: Union[str, Sequence[str], None] = "87465391ba17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "disbursement_records",
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        op.f("ix_disbursement_records_correlation_id"),
        "disbursement_records",
        ["correlation_id"],
        unique=False,
    )

    op.create_table(
        "disbursement_idempotency",
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
    op.drop_table("disbursement_idempotency")
    op.drop_index(
        op.f("ix_disbursement_records_correlation_id"),
        table_name="disbursement_records",
    )
    op.drop_column("disbursement_records", "correlation_id")
