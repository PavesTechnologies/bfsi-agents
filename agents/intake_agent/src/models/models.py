from typing import Optional
import datetime
import decimal
import uuid
import enum


from sqlalchemy import BigInteger, Boolean, CHAR, CheckConstraint, Date, DateTime, ForeignKeyConstraint, Integer, JSON, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, Uuid, text,LargeBinary,Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from src.utils.migration_database import Base   # <-- import Base



class AuditLogs(Base):
    __tablename__ = 'audit_logs'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='audit_logs_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[dict] = mapped_column(JSONB, nullable=False)
    old_data: Mapped[Optional[dict]] = mapped_column(JSON)
    new_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class CallbackStatus(Base):
    __tablename__ = 'callback_status'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='callback_status_pkey'),
        UniqueConstraint('request_id', name='callback_status_request_id_key')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    callback_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))


class IntakeIdempotency(Base):
    __tablename__ = 'intake_idempotency'
    __table_args__ = (
        PrimaryKeyConstraint('request_id', name='intake_idempotency_pkey'),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    app_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    response_payload: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))


class LoanApplication(Base):
    __tablename__ = 'loan_application'
    __table_args__ = (
        CheckConstraint("credit_type::text = ANY (ARRAY['individual'::character varying, 'joint'::character varying]::text[])", name='loan_application_credit_type_check'),
        CheckConstraint('preferred_payment_day >= 1 AND preferred_payment_day <= 28', name='loan_application_preferred_payment_day_check'),
        CheckConstraint('requested_amount > 0::numeric', name='loan_application_requested_amount_check'),
        PrimaryKeyConstraint('application_id', name='loan_application_pkey')
    )

    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    loan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    credit_type: Mapped[Optional[str]] = mapped_column(String(20))
    loan_purpose: Mapped[Optional[str]] = mapped_column(String(50))
    requested_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 2))
    requested_term_months: Mapped[Optional[int]] = mapped_column(Integer)
    preferred_payment_day: Mapped[Optional[int]] = mapped_column(Integer)
    origination_channel: Mapped[Optional[str]] = mapped_column(String(20))
    application_status: Mapped[Optional[str]] = mapped_column(String(30))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    applicant: Mapped[list['Applicant']] = relationship('Applicant', back_populates='application', lazy="selectin")
    document: Mapped[list['Document']] = relationship('Document', back_populates='application', lazy="selectin")
    pgsql_documents: Mapped[list["PgsqlDocument"]] = relationship(
    "PgsqlDocument",
    back_populates="application",
    cascade="all, delete-orphan",
    lazy="selectin",
    )


class Applicant(Base):
    __tablename__ = 'applicant'
    __table_args__ = (
        CheckConstraint("applicant_role::text = ANY (ARRAY['primary'::character varying, 'co_applicant'::character varying]::text[])", name='applicant_applicant_role_check'),
        ForeignKeyConstraint(['application_id'], ['loan_application.application_id'], ondelete='CASCADE', name='fk_applicant_application'),
        PrimaryKeyConstraint('applicant_id', name='applicant_pkey'),
        UniqueConstraint('email', name='uq_applicant_email')
    )

    applicant_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    applicant_role: Mapped[Optional[str]] = mapped_column(String(20))
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    suffix: Mapped[Optional[str]] = mapped_column(String(10))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    ssn_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    ssn_last4: Mapped[Optional[str]] = mapped_column(CHAR(4))
    itin_number: Mapped[Optional[str]] = mapped_column(String(15))
    citizenship_status: Mapped[Optional[str]] = mapped_column(String(30))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    application: Mapped['LoanApplication'] = relationship('LoanApplication', back_populates='applicant', lazy="selectin")
    address: Mapped[list['Address']] = relationship('Address', back_populates='applicant', lazy="selectin")
    asset: Mapped[list['Asset']] = relationship('Asset', back_populates='applicant', lazy="selectin")
    employment: Mapped[list['Employment']] = relationship('Employment', back_populates='applicant', lazy="selectin")
    income: Mapped[list['Income']] = relationship('Income', back_populates='applicant', lazy="selectin")
    liability: Mapped[list['Liability']] = relationship('Liability', back_populates='applicant', lazy="selectin")


class Document(Base):
    __tablename__ = 'document'
    __table_args__ = (
        ForeignKeyConstraint(['application_id'], ['loan_application.application_id'], ondelete='CASCADE', name='fk_document_application'),
        PrimaryKeyConstraint('document_id', name='document_pkey')
    )

    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[Optional[str]] = mapped_column(String(50))
    uploaded_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    application: Mapped['LoanApplication'] = relationship('LoanApplication', back_populates='document', lazy="selectin")


class Address(Base):
    __tablename__ = 'address'
    __table_args__ = (
        CheckConstraint("address_type::text = ANY (ARRAY['current'::character varying, 'permanent'::character varying, 'mailing'::character varying]::text[])", name='address_address_type_check'),
        CheckConstraint("housing_status::text = ANY (ARRAY['own'::character varying, 'rent'::character varying]::text[])", name='address_housing_status_check'),
        CheckConstraint('months_at_address >= 0 AND months_at_address <= 11', name='address_months_at_address_check'),
        CheckConstraint('years_at_address >= 0 AND years_at_address <= 50', name='address_years_at_address_check'),
        ForeignKeyConstraint(['applicant_id'], ['applicant.applicant_id'], ondelete='CASCADE', name='fk_address_applicant'),
        PrimaryKeyConstraint('address_id', name='address_pkey')
    )

    address_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    applicant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    address_type: Mapped[Optional[str]] = mapped_column(String(20))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("'USA'::character varying"))
    housing_status: Mapped[Optional[str]] = mapped_column(String(30))
    monthly_housing_payment: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 2))
    years_at_address: Mapped[Optional[int]] = mapped_column(Integer)
    months_at_address: Mapped[Optional[int]] = mapped_column(Integer)
    address_verified: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    applicant: Mapped['Applicant'] = relationship('Applicant', back_populates='address', lazy="selectin")


class Asset(Base):
    __tablename__ = 'asset'
    __table_args__ = (
        CheckConstraint("ownership_type::text = ANY (ARRAY['individual'::character varying, 'joint'::character varying]::text[])", name='asset_ownership_type_check'),
        CheckConstraint('value >= 0::numeric', name='asset_value_check'),
        ForeignKeyConstraint(['applicant_id'], ['applicant.applicant_id'], ondelete='CASCADE', name='fk_asset_applicant'),
        PrimaryKeyConstraint('asset_id', name='asset_pkey')
    )

    asset_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    applicant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    asset_type: Mapped[Optional[str]] = mapped_column(String(30))
    institution_name: Mapped[Optional[str]] = mapped_column(String(255))
    value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2))
    ownership_type: Mapped[Optional[str]] = mapped_column(String(20))
    asset_verified: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    applicant: Mapped['Applicant'] = relationship('Applicant', back_populates='asset', lazy="selectin")


class Employment(Base):
    __tablename__ = 'employment'
    __table_args__ = (
        CheckConstraint('experience >= 0', name='employment_experience_check'),
        ForeignKeyConstraint(['applicant_id'], ['applicant.applicant_id'], ondelete='CASCADE', name='fk_employment_applicant'),
        PrimaryKeyConstraint('employment_id', name='employment_pkey')
    )

    employment_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    applicant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    employment_type: Mapped[Optional[str]] = mapped_column(String(30))
    employment_status: Mapped[Optional[str]] = mapped_column(String(20))
    employer_name: Mapped[Optional[str]] = mapped_column(String(255))
    employer_phone: Mapped[Optional[str]] = mapped_column(String(20))
    employer_address: Mapped[Optional[str]] = mapped_column(Text)
    job_title: Mapped[Optional[str]] = mapped_column(String(100))
    start_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    experience: Mapped[Optional[int]] = mapped_column(Integer)
    self_employed_flag: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    family_employment: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    gross_monthly_income: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 2))
    employment_verified: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    applicant: Mapped['Applicant'] = relationship('Applicant', back_populates='employment', lazy="selectin")


class Income(Base):
    __tablename__ = 'income'
    __table_args__ = (
        CheckConstraint('monthly_amount >= 0::numeric', name='income_monthly_amount_check'),
        ForeignKeyConstraint(['applicant_id'], ['applicant.applicant_id'], ondelete='CASCADE', name='fk_income_applicant'),
        PrimaryKeyConstraint('income_id', name='income_pkey')
    )

    income_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    applicant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    income_type: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    monthly_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 2))
    income_frequency: Mapped[Optional[str]] = mapped_column(String(20))

    applicant: Mapped['Applicant'] = relationship('Applicant', back_populates='income', lazy="selectin")


class Liability(Base):
    __tablename__ = 'liability'
    __table_args__ = (
        CheckConstraint('days_delinquent >= 0', name='liability_days_delinquent_check'),
        CheckConstraint('monthly_payment >= 0::numeric', name='liability_monthly_payment_check'),
        CheckConstraint('months_remaining >= 0', name='liability_months_remaining_check'),
        CheckConstraint('outstanding_balance >= 0::numeric', name='liability_outstanding_balance_check'),
        ForeignKeyConstraint(['applicant_id'], ['applicant.applicant_id'], ondelete='CASCADE', name='fk_liability_applicant'),
        PrimaryKeyConstraint('liability_id', name='liability_pkey')
    )

    liability_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    applicant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    liability_type: Mapped[Optional[str]] = mapped_column(String(50))
    creditor_name: Mapped[Optional[str]] = mapped_column(String(255))
    outstanding_balance: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 2))
    monthly_payment: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 2))
    months_remaining: Mapped[Optional[int]] = mapped_column(Integer)
    co_signed: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    federal_debt: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    delinquent_flag: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    days_delinquent: Mapped[Optional[int]] = mapped_column(Integer)

    applicant: Mapped['Applicant'] = relationship('Applicant', back_populates='liability', lazy="selectin")

class IntakeValidationResult(Base):
    __tablename__ = "intake_validation_result"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    field_name: Mapped[str] = mapped_column(String, nullable=False)
    reason_code: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, default=datetime.datetime.utcnow)



class PgsqlDocument(Base):
    __tablename__ = "pgsqldocument"
    __table_args__ = (
        ForeignKeyConstraint(
            ["application_id"],
            ["loan_application.application_id"],
            ondelete="CASCADE",
            name="fk_pgsqldocument_application",
        ),
        PrimaryKeyConstraint("id", name="pgsqldocument_pkey"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))

    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Actual file bytes (PDF / JPG)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )

    application = relationship(
        "LoanApplication",
        back_populates="pgsql_documents",
        lazy="selectin",
    )