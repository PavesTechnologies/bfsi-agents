"""initial schema - bank admin tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-05-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Roles ---
    op.create_table(
        "bank_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- Users ---
    op.create_table(
        "bank_users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["bank_roles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bank_users_email", "bank_users", ["email"], unique=True)

    # --- Sessions ---
    op.create_table(
        "bank_sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["bank_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- Audit Log ---
    op.create_table(
        "bank_admin_audit_log",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("before_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("after_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["bank_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_user_id", "bank_admin_audit_log", ["user_id"])
    op.create_index("ix_audit_log_resource", "bank_admin_audit_log", ["resource_type", "resource_id"])

    # --- Rule Categories ---
    op.create_table(
        "rule_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- Bank Rules ---
    op.create_table(
        "bank_rules",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("rule_key", sa.String(100), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("current_value", postgresql.JSONB(), nullable=False),
        sa.Column("default_value", postgresql.JSONB(), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("validation_schema", postgresql.JSONB(), nullable=True),
        sa.Column("risk_level", sa.String(20), server_default="low", nullable=False),
        sa.Column("requires_approval", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["rule_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bank_rules_key", "bank_rules", ["rule_key"], unique=True)

    # --- Rule History ---
    op.create_table(
        "bank_rule_history",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("old_value", postgresql.JSONB(), nullable=True),
        sa.Column("new_value", postgresql.JSONB(), nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approval_status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("reviewer_comment", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["rule_id"], ["bank_rules.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["bank_users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["bank_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rule_history_rule_id", "bank_rule_history", ["rule_id"])
    op.create_index("ix_rule_history_status", "bank_rule_history", ["approval_status"])

    # --- RAG Documents ---
    op.create_table(
        "rag_documents",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("collection_name", sa.String(100), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), server_default="PENDING", nullable=False),
        sa.Column("qdrant_point_ids", postgresql.JSONB(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=True),
        sa.Column("ingestion_log", postgresql.JSONB(), nullable=True),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column("replaced_document_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by"], ["bank_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_documents_collection", "rag_documents", ["collection_name"])
    op.create_index("ix_rag_documents_status", "rag_documents", ["status"])

    # --- RAG Ingestion Jobs ---
    op.create_table(
        "rag_ingestion_jobs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(30), server_default="QUEUED", nullable=False),
        sa.Column("progress_pct", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["rag_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed roles
    op.execute("""
        INSERT INTO bank_roles (name, description) VALUES
        ('SUPER_ADMIN', 'Full access - can manage users, approve rules, delete documents'),
        ('CREDIT_MANAGER', 'Can edit low-risk rules and upload documents'),
        ('UNDERWRITER', 'Read-only access to applications'),
        ('COMPLIANCE_OFFICER', 'Can upload/replace RAG documents and view audit logs'),
        ('AUDITOR', 'Read-only access with audit log and export rights'),
        ('VIEWER', 'Read-only access to applications only')
    """)

    # Seed rule categories
    op.execute("""
        INSERT INTO rule_categories (name, description) VALUES
        ('credit_score', 'CIBIL/Bureau score thresholds per risk tier'),
        ('dti', 'Debt-to-Income ratio thresholds'),
        ('utilization', 'Credit utilization limits'),
        ('exposure', 'Total debt exposure limits'),
        ('public_record', 'Public record disqualification rules'),
        ('behavior', 'Payment behavior and delinquency rules'),
        ('inquiry', 'Hard inquiry velocity limits'),
        ('income', 'Income verification and multiplier rules')
    """)

    # Seed default bank rules
    op.execute("""
        INSERT INTO bank_rules (category_id, rule_key, display_name, description, current_value, default_value, data_type, validation_schema, risk_level, requires_approval) VALUES
        (1, 'min_cibil_score_tier_a', 'Min CIBIL Score - Tier A (Prime)', 'Minimum CIBIL score for Tier A approval', '{"value": 750}', '{"value": 750}', 'number', '{"min": 300, "max": 900}', 'high', true),
        (1, 'min_cibil_score_tier_b', 'Min CIBIL Score - Tier B (Good)', 'Minimum CIBIL score for Tier B approval', '{"value": 700}', '{"value": 700}', 'number', '{"min": 300, "max": 900}', 'low', false),
        (1, 'min_cibil_score_tier_c', 'Min CIBIL Score - Tier C (Fair)', 'Minimum CIBIL score for Tier C approval', '{"value": 650}', '{"value": 650}', 'number', '{"min": 300, "max": 900}', 'low', false),
        (1, 'decline_floor_score', 'Decline Floor Score', 'CIBIL score below which application is always declined', '{"value": 600}', '{"value": 600}', 'number', '{"min": 300, "max": 700}', 'high', true),
        (2, 'max_dti_threshold', 'Max Debt-to-Income Ratio', 'Maximum allowed DTI for any approval', '{"value": 0.50}', '{"value": 0.50}', 'number', '{"min": 0.1, "max": 0.8}', 'low', false),
        (2, 'max_dti_tier_a', 'Max DTI - Tier A', 'Maximum DTI for Tier A borrowers', '{"value": 0.40}', '{"value": 0.40}', 'number', '{"min": 0.1, "max": 0.8}', 'low', false),
        (3, 'max_utilization_approve', 'Max Utilization for Approval', 'Maximum credit utilization allowed for approval', '{"value": 0.70}', '{"value": 0.70}', 'number', '{"min": 0.1, "max": 1.0}', 'low', false),
        (3, 'max_utilization_tier_a', 'Max Utilization - Tier A', 'Maximum credit utilization for Tier A', '{"value": 0.30}', '{"value": 0.30}', 'number', '{"min": 0.1, "max": 1.0}', 'low', false),
        (4, 'max_approved_amount', 'Max Approvable Loan Amount', 'Maximum single loan amount that can be approved', '{"value": 5000000}', '{"value": 5000000}', 'number', '{"min": 100000, "max": 50000000}', 'high', true),
        (4, 'income_multiplier_max', 'Max Income Multiplier', 'Maximum loan amount as multiple of annual income', '{"value": 10}', '{"value": 10}', 'number', '{"min": 1, "max": 30}', 'low', false),
        (5, 'disqualify_active_bankruptcy', 'Disqualify Active Bankruptcy', 'Decline all applications with active bankruptcy', '{"value": true}', '{"value": true}', 'boolean', null, 'high', true),
        (5, 'disqualify_wilful_default', 'Disqualify Wilful Default', 'Decline all applications tagged as wilful defaulters', '{"value": true}', '{"value": true}', 'boolean', null, 'high', true),
        (6, 'max_dpd_30_count', 'Max DPD 30+ in 12 months', 'Maximum number of 30+ DPD events in last 12 months', '{"value": 2}', '{"value": 2}', 'number', '{"min": 0, "max": 12}', 'low', false),
        (7, 'max_hard_inquiries_6m', 'Max Hard Inquiries (6 months)', 'Maximum hard credit inquiries in last 6 months', '{"value": 4}', '{"value": 4}', 'number', '{"min": 0, "max": 20}', 'low', false),
        (8, 'min_monthly_income', 'Min Monthly Income', 'Minimum monthly income required for any approval', '{"value": 25000}', '{"value": 25000}', 'number', '{"min": 5000, "max": 500000}', 'low', false),
        (8, 'origination_fee_pct', 'Origination Fee Percentage', 'Percentage charged as origination fee', '{"value": 0.025}', '{"value": 0.025}', 'number', '{"min": 0, "max": 0.1}', 'high', true)
    """)


def downgrade() -> None:
    op.drop_table("rag_ingestion_jobs")
    op.drop_table("rag_documents")
    op.drop_table("bank_rule_history")
    op.drop_table("bank_rules")
    op.drop_table("rule_categories")
    op.drop_table("bank_admin_audit_log")
    op.drop_table("bank_sessions")
    op.drop_table("bank_users")
    op.drop_table("bank_roles")
