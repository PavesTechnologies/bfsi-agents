"""PI Added

Revision ID: d40cb623ba09
Revises: d85d179ba7c2
Create Date: 2026-02-09 18:58:46.354005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd40cb623ba09'
down_revision: Union[str, Sequence[str], None] = 'd85d179ba7c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

gender_enum = postgresql.ENUM(
    'MALE',
    'FEMALE',
    'NON_BINARY',
    'OTHER',
    'PREFER_NOT_TO_SAY',
    name='gender_enum'
)


def upgrade():
    # 1️⃣ Create enum
    gender_enum.create(op.get_bind(), checkfirst=True)

    # 2️⃣ Add columns as NULLABLE FIRST (IMPORTANT)
    op.add_column(
        'applicant',
        sa.Column('phone_number', sa.String(length=20), nullable=True)
    )

    op.add_column(
        'applicant',
        sa.Column('gender', gender_enum, nullable=True)
    )

    # 3️⃣ Backfill existing rows
    op.execute("""
        UPDATE applicant
        SET phone_number = '0000000000'
        WHERE phone_number IS NULL
    """)

    op.execute("""
        UPDATE applicant
        SET gender = 'PREFER_NOT_TO_SAY'
        WHERE gender IS NULL
    """)

    # 4️⃣ Enforce NOT NULL (FINAL STATE)
    op.alter_column(
        'applicant',
        'phone_number',
        nullable=False
    )

    op.alter_column(
        'applicant',
        'gender',
        nullable=False
    )


def downgrade():
    # Allow NULLs again
    op.alter_column('applicant', 'gender', nullable=True)
    op.alter_column('applicant', 'phone_number', nullable=True)

    # Drop columns
    op.drop_column('applicant', 'gender')
    op.drop_column('applicant', 'phone_number')

    # Drop enum
    gender_enum.drop(op.get_bind(), checkfirst=True)
