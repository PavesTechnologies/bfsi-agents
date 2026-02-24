from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field
from src.models.enums import Gender
from src.utils.validation.blocking_aggregator import (
    BlockingValidationSummary,
)


class CreditType(StrEnum):
    individual = "individual"
    joint = "joint"


class ApplicantRole(StrEnum):
    primary = "primary"
    co_applicant = "co_applicant"


class AddressType(StrEnum):
    current = "current"
    permanent = "permanent"
    mailing = "mailing"


class HousingStatus(StrEnum):
    own = "own"
    rent = "rent"


class OwnershipType(StrEnum):
    individual = "individual"
    joint = "joint"


class AddressSchema(BaseModel):
    address_type: AddressType
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    zip_code: str
    country: str
    housing_status: HousingStatus
    monthly_housing_payment: float | None = None
    years_at_address: int = Field(..., ge=0, le=50)
    months_at_address: int = Field(..., ge=0, le=11)


class EmploymentSchema(BaseModel):
    employment_type: str
    employment_status: str
    employer_name: str | None = None
    employer_phone: str | None = None
    employer_address: str | None = None
    job_title: str | None = None
    start_date: date | None = None
    experience: int | None = None
    self_employed_flag: bool = False
    family_employment: bool = False
    gross_monthly_income: float | None = None


class IncomeSchema(BaseModel):
    income_type: str
    description: str | None = None
    monthly_amount: float = Field(..., ge=0)
    income_frequency: str


class AssetSchema(BaseModel):
    asset_type: str
    institution_name: str
    value: float = Field(..., ge=0)
    ownership_type: OwnershipType


class LiabilitySchema(BaseModel):
    liability_type: str
    creditor_name: str
    outstanding_balance: float = Field(..., ge=0)
    monthly_payment: float = Field(..., ge=0)
    months_remaining: int = Field(..., ge=0)
    co_signed: bool = False
    federal_debt: bool = False
    delinquent: bool = False


class ApplicantSchema(BaseModel):
    applicant_role: ApplicantRole

    # ⚠️ Dirty input allowed
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    suffix: str | None = None

    date_of_birth: date | None = None

    # ⚠️ NO length / regex constraints here
    ssn_no: str | None = None
    ssn_last4: str | None = None
    itin_number: str | None = None
    citizenship_status: str | None = None
    email: str | None = None

    # ✅ REQUIRED (DB NOT NULL)
    phone_number: str
    gender: Gender

    # ⚠️ Collections default to empty
    addresses: list[AddressSchema] = []
    employment: EmploymentSchema | None = None
    incomes: list[IncomeSchema] = []
    assets: list[AssetSchema] = []
    liabilities: list[LiabilitySchema] = []


class LoanIntakeRequest(BaseModel):
    # -------------------------
    # LOAN_APPLICATION
    # -------------------------
    request_id: UUID
    callback_url: str

    # ⚠️ optional at intake stage
    app_id: UUID | None = None
    payload: dict | None = None

    loan_type: str
    credit_type: CreditType
    loan_purpose: str

    requested_amount: float = Field(..., gt=0)
    requested_term_months: int
    preferred_payment_day: int = Field(..., ge=1, le=28)

    origination_channel: str
    application_status: str = "submitted"

    # -------------------------
    # RELATIONSHIPS
    # -------------------------
    applicants: list[ApplicantSchema]
    # documents: Optional[List[DocumentSchema]] = []


class ValidationIssue(BaseModel):
    """Represents a non-blocking validation failure during intake processing."""

    field: str = Field(
        ..., description="Field path that failed validation (e.g., applicant[0].email)"
    )
    reason_code: str = Field(
        ...,
        description="Machine-readable reason code (e.g.,\
              non_blocking_validation, duplicate_email)",
    )
    message: str = Field(..., description="Human-friendly validation error message")


class LoanIntakeResponse(BaseModel):
    application_id: UUID
    timestamp: datetime
    validation_issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="Non-blocking validation issues collected during intake processing",
    )
    validation_summary: BlockingValidationSummary | None = Field(
        default=None,
        description="Blocking validation summary collected during intake processing",
    )
