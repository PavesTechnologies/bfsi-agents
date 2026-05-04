"""india sprint1 fields

Revision ID: a1b2c3d4e5f6
Revises: 7f27cb9132e4
Create Date: 2026-04-25 00:00:00.000000

Adds India-specific fields to applicant table and updates pgsqldocument
document_type constraint to India document types.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7f27cb9132e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Applicant: new India identity fields ---
    op.add_column('applicant', sa.Column('aadhaar_vid', sa.String(16), nullable=True))
    op.add_column('applicant', sa.Column('pan_verified', sa.Boolean(), nullable=True,
                                         server_default=sa.text('false')))
    op.add_column('applicant', sa.Column('ckyc_number', sa.String(14), nullable=True))
    op.add_column('applicant', sa.Column('preferred_language', sa.String(10), nullable=True,
                                          server_default=sa.text("'en'")))

    # --- pgsqldocument: replace document_type constraint with India types ---
    op.drop_constraint('pgsqldocument_document_type_check', 'pgsqldocument', type_='check')
    op.create_check_constraint(
        'pgsqldocument_document_type_check',
        'pgsqldocument',
        "document_type::text = ANY (ARRAY["
        "'aadhaar_card'::text, "
        "'pan_card'::text, "
        "'voter_id'::text, "
        "'driving_license_india'::text, "
        "'passport'::text, "
        "'bank_statement'::text, "
        "'itr'::text, "
        "'form_16'::text, "
        "'salary_slip'::text, "
        "'utility_bill'::text, "
        "'photo'::text, "
        "'address_proof'::text, "
        "'gst_certificate'::text, "
        "'udyam_certificate'::text"
        "])",
    )


def downgrade() -> None:
    op.drop_column('applicant', 'preferred_language')
    op.drop_column('applicant', 'ckyc_number')
    op.drop_column('applicant', 'pan_verified')
    op.drop_column('applicant', 'aadhaar_vid')

    op.drop_constraint('pgsqldocument_document_type_check', 'pgsqldocument', type_='check')
    op.create_check_constraint(
        'pgsqldocument_document_type_check',
        'pgsqldocument',
        "document_type::text = ANY (ARRAY["
        "'ssn_card'::text, 'passport'::text, 'drivers_license'::text, "
        "'state_id'::text, 'itr'::text, 'w2'::text, 'aadhaar_card'::text, "
        "'pan_card'::text, 'pay_stub'::text, 'bank_statement'::text, "
        "'tax_return'::text, 'utility_bill'::text, 'lease_agreement'::text, 'photo'::text"
        "])",
    )
