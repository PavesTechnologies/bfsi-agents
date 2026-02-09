"""col correction

Revision ID: b31327225042
Revises: 1a1ce6612ea2
Create Date: 2026-02-09 15:39:57.911175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b31327225042'
down_revision: Union[str, Sequence[str], None] = '1a1ce6612ea2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


applicant_status_enum = postgresql.ENUM(
    'SUBMITTED',
    'UNDER_REVIEW',
    'REVISION_REQUIRED',
    'APPROVED',
    'REJECTED',
    name='applicant_status_enum'
)

def upgrade():
    # 1️⃣ Ensure enum exists
    applicant_status_enum.create(op.get_bind(), checkfirst=True)

    # 2️⃣ Normalize existing data (VERY IMPORTANT)
    op.execute("""
        UPDATE loan_application
        SET application_status = UPPER(application_status)
        WHERE application_status IS NOT NULL
    """)

    # Optional: handle legacy values
    op.execute("""
        UPDATE loan_application
        SET application_status = 'SUBMITTED'
        WHERE application_status IS NULL
    """)

    # 3️⃣ Alter column WITH explicit cast
    op.execute("""
        ALTER TABLE loan_application
        ALTER COLUMN application_status
        TYPE applicant_status_enum
        USING application_status::applicant_status_enum
    """)

def downgrade():
    op.execute("""
        ALTER TABLE loan_application
        ALTER COLUMN application_status
        TYPE VARCHAR
    """)

    applicant_status_enum.drop(op.get_bind(), checkfirst=True)