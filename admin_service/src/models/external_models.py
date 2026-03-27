"""
Read-only SQLAlchemy Core Table definitions for all agent databases.

These are NOT ORM mapped classes — they are Table objects used for Core
select() queries against external (read-only) databases.

Databases:
  defaultdb         — intake_agent
  kyc_agent         — kyc_agent
  decisioning_agent — decisioning_agent
  disbursment_agent — disbursment_agent (note: intentional typo matches actual DB name)
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

# ---------------------------------------------------------------------------
# defaultdb — intake_agent tables
# ---------------------------------------------------------------------------
intake_metadata = MetaData()

loan_application_table = Table(
    "loan_application",
    intake_metadata,
    Column("application_id", UUID(as_uuid=True), primary_key=True),
    Column("loan_type", String(50)),
    Column("credit_type", String(20)),
    Column("loan_purpose", String(50)),
    Column("requested_amount", Numeric(12, 2)),
    Column("requested_term_months", Integer),
    Column("preferred_payment_day", Integer),
    Column("origination_channel", String(20)),
    Column("application_status", String(30)),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
)

applicant_table = Table(
    "applicant",
    intake_metadata,
    Column("applicant_id", UUID(as_uuid=True), primary_key=True),
    Column("application_id", UUID(as_uuid=True)),
    Column("first_name", String(100)),
    Column("middle_name", String(100)),
    Column("last_name", String(100)),
    Column("suffix", String(10)),
    Column("date_of_birth", Date),
    Column("applicant_role", String(20)),
    Column("email", Text),
    Column("ssn_last4", String(4)),
    Column("phone_number", Text),
    Column("gender", String(30)),
    Column("citizenship_status", String(30)),
    Column("itin_number", String(15)),
    Column("created_at", DateTime(timezone=True)),
)

address_table = Table(
    "address",
    intake_metadata,
    Column("address_id", UUID(as_uuid=True), primary_key=True),
    Column("applicant_id", UUID(as_uuid=True)),
    Column("address_type", String(20)),
    Column("address_line1", String(255)),
    Column("address_line2", String(255)),
    Column("city", String(100)),
    Column("state", String(30)),
    Column("zip_code", String(10)),
    Column("country", String(50)),
    Column("housing_status", String(30)),
    Column("monthly_housing_payment", Numeric(10, 2)),
    Column("years_at_address", Integer),
    Column("months_at_address", Integer),
    Column("address_verified", Boolean),
)

employment_table = Table(
    "employment",
    intake_metadata,
    Column("employment_id", UUID(as_uuid=True), primary_key=True),
    Column("applicant_id", UUID(as_uuid=True)),
    Column("employment_type", String(30)),
    Column("employment_status", String(20)),
    Column("employer_name", String(255)),
    Column("employer_phone", String(20)),
    Column("job_title", String(100)),
    Column("start_date", Date),
    Column("experience", Integer),
    Column("self_employed_flag", Boolean),
    Column("gross_monthly_income", Numeric(12, 2)),
    Column("employment_verified", Boolean),
)

income_table = Table(
    "income",
    intake_metadata,
    Column("income_id", UUID(as_uuid=True), primary_key=True),
    Column("applicant_id", UUID(as_uuid=True)),
    Column("income_type", String(50)),
    Column("description", Text),
    Column("monthly_amount", Numeric(12, 2)),
    Column("income_frequency", String(20)),
)

asset_table = Table(
    "asset",
    intake_metadata,
    Column("asset_id", UUID(as_uuid=True), primary_key=True),
    Column("applicant_id", UUID(as_uuid=True)),
    Column("asset_type", String(30)),
    Column("institution_name", String(255)),
    Column("value", Numeric(14, 2)),
    Column("ownership_type", String(20)),
    Column("asset_verified", Boolean),
)

liability_table = Table(
    "liability",
    intake_metadata,
    Column("liability_id", UUID(as_uuid=True), primary_key=True),
    Column("applicant_id", UUID(as_uuid=True)),
    Column("liability_type", String(50)),
    Column("creditor_name", String(255)),
    Column("outstanding_balance", Numeric(14, 2)),
    Column("monthly_payment", Numeric(12, 2)),
    Column("months_remaining", Integer),
    Column("co_signed", Boolean),
    Column("federal_debt", Boolean),
    Column("delinquent_flag", Boolean),
)

# pgsqldocument has richer metadata than legacy `document` table
pgsql_document_table = Table(
    "pgsqldocument",
    intake_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("application_id", UUID(as_uuid=True)),
    Column("document_type", String(50)),
    Column("file_name", String),
    Column("mime_type", String(100)),
    Column("file_size", BigInteger),
    Column("uploaded_at", DateTime(timezone=True)),
    Column("is_low_quality", Boolean),
    Column("quality_metadata", JSONB),
)

# ---------------------------------------------------------------------------
# kyc_agent tables
# ---------------------------------------------------------------------------
kyc_metadata = MetaData()

kyc_cases_table = Table(
    "kyc_cases",
    kyc_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("applicant_id", UUID(as_uuid=True)),   # NOTE: applicant_id, not application_id
    Column("status", String(20)),                  # PENDING | PASSED | REVIEW | FAILED
    Column("confidence_score", Float),
    Column("rules_version", String(50)),
    Column("created_at", DateTime(timezone=True)),
    Column("completed_at", DateTime(timezone=True)),
)

aml_checks_table = Table(
    "aml_checks",
    kyc_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("kyc_id", UUID(as_uuid=True)),
    Column("ofac_match", Boolean),
    Column("ofac_confidence", Float),
    Column("pep_match", Boolean),
    Column("aml_score", Float),
    Column("flags", JSONB),
    Column("created_at", DateTime(timezone=True)),
)

identity_checks_table = Table(
    "identity_checks",
    kyc_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("kyc_id", UUID(as_uuid=True)),
    Column("applicant_id", String),
    Column("final_status", String),
    Column("aggregated_score", Float),
    Column("hard_fail_triggered", Boolean),
    Column("ssn_valid", Boolean),
    Column("name_ssn_match", Boolean),
    Column("dob_ssn_match", Boolean),
    Column("deceased_flag", Boolean),
    Column("created_at", DateTime(timezone=True)),
)

risk_decisions_table = Table(
    "risk_decisions",
    kyc_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("kyc_id", UUID(as_uuid=True)),
    Column("final_status", String(20)),   # PASS | REVIEW | FAIL
    Column("aggregated_score", Float),
    Column("hard_fail_triggered", Boolean),
    Column("decision_reason", Text),
    Column("created_at", DateTime(timezone=True)),
)

# ---------------------------------------------------------------------------
# decisioning_agent tables
# ---------------------------------------------------------------------------
decisioning_metadata = MetaData()

underwriting_decisions_table = Table(
    "underwriting_decisions",
    decisioning_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("application_id", String(50)),
    Column("decision", String(20)),          # APPROVE | DECLINE | COUNTER_OFFER
    Column("risk_tier", String(10)),
    Column("risk_score", Float),
    Column("approved_amount", Numeric(12, 2)),
    Column("disbursement_amount", Numeric(12, 2)),
    Column("interest_rate", Float),
    Column("tenure_months", Integer),
    Column("explanation", Text),
    Column("decline_reason", Text),
    Column("reasoning_steps", JSONB),
    Column("counter_offer_data", JSONB),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
)

# ---------------------------------------------------------------------------
# disbursment_agent tables (note: intentional typo matches actual DB name)
# ---------------------------------------------------------------------------
disbursement_metadata = MetaData()

disbursement_records_table = Table(
    "disbursement_records",
    disbursement_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("application_id", String(50)),
    Column("transaction_id", String(100)),
    Column("status", String(20)),
    Column("disbursement_amount", Numeric(12, 2)),
    Column("transfer_timestamp", DateTime(timezone=True)),
    Column("monthly_emi", Numeric(12, 2)),
    Column("total_interest", Numeric(12, 2)),
    Column("total_repayment", Numeric(12, 2)),
    Column("repayment_schedule", JSONB),
    Column("receipt_payload", JSONB),
    Column("created_at", DateTime(timezone=True)),
)
