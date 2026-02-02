from typing import List, Optional, Dict
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum

class CreditType(str, Enum):
    individual = "individual"
    joint = "joint"

class ApplicantRole(str, Enum):
    primary = "primary"
    co_applicant = "co_applicant"
    
class AddressType(str, Enum):
    current = "current"
    permanent = "permanent"
    mailing = "mailing"
    
class HousingStatus(str, Enum):
    own = "own"
    rent = "rent"
    
class OwnershipType(str, Enum):
    individual = "individual"
    joint = "joint"

class AddressSchema(BaseModel):
    address_type: AddressType
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str 
    zip_code: str
    country: str 
    housing_status: HousingStatus
    monthly_housing_payment: Optional[float] = None
    years_at_address: int = Field(..., ge=0, le=50)
    months_at_address: int = Field(..., ge=0, le=11)

class EmploymentSchema(BaseModel):
    employment_type: str
    employment_status: str
    employer_name: Optional[str] = None
    employer_phone: Optional[str] = None
    employer_address: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[date] = None
    experience: Optional[int] = None
    self_employed_flag: bool = False
    family_employment: bool = False
    gross_monthly_income: Optional[float] = None

class IncomeSchema(BaseModel):
    income_type: str
    description: Optional[str] = None
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
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None

    date_of_birth: Optional[date] = None

    # ⚠️ NO length / regex constraints here
    ssn_last4: Optional[str] = None
    itin_number: Optional[str] = None
    citizenship_status: Optional[str] = None
    email: Optional[str] = None

    # ⚠️ Collections default to empty
    addresses: List[AddressSchema] = []
    employment: Optional[EmploymentSchema] = None
    incomes: List[IncomeSchema] = []
    assets: List[AssetSchema] = []
    liabilities: List[LiabilitySchema] = []
class LoanIntakeRequest(BaseModel):
    # -------------------------
    # LOAN_APPLICATION
    # -------------------------
    request_id: UUID
    callback_url: str

    # ⚠️ optional at intake stage
    app_id: Optional[UUID] = None
    payload: Optional[Dict] = None
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
    applicants: List[ApplicantSchema]
    # documents: Optional[List[DocumentSchema]] = []

class LoanIntakeResponse(BaseModel):
    application_id: UUID
    timestamp: datetime