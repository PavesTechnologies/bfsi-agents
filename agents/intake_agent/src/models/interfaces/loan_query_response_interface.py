import decimal
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from src.models.enums import ApplicantStatus, Gender


class PgsqlDocumentResponse(BaseModel):
    id: UUID
    document_type: str
    file_name: str
    mime_type: str
    file_size: int
    uploaded_at: datetime
    is_low_quality: bool
    quality_metadata: dict | None

    model_config = ConfigDict(from_attributes=True)


class ApplicantResponse(BaseModel):
    applicant_id: UUID
    first_name: str
    last_name: str
    email: str | None
    phone_number: str
    gender: Gender

    model_config = ConfigDict(from_attributes=True)


class LoanDetailsResponse(BaseModel):
    application_id: UUID
    loan_type: str
    credits_type: str
    application_status: ApplicantStatus
    created_at: datetime
    credit_type: str
    loan_purpose: str
    requested_amount: decimal.Decimal
    requested_term_months: int
    preferred_payment_day: int
    origination_channel: str

    applicants: list[ApplicantResponse]
    documents: list[PgsqlDocumentResponse]

    model_config = ConfigDict(from_attributes=True)
