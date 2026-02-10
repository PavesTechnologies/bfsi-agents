from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from src.models.enums import ApplicantStatus, Gender
import decimal

class PgsqlDocumentResponse(BaseModel):
    id: UUID
    document_type: str
    file_name: str
    mime_type: str
    file_size: int
    uploaded_at: datetime
    is_low_quality: bool
    quality_metadata: Optional[dict]

    class Config:
        orm_mode = True


class ApplicantResponse(BaseModel):
    applicant_id: UUID
    first_name: str
    last_name: str
    email: Optional[str]
    phone_number: str
    gender: Gender

    class Config:
        orm_mode = True


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

    applicants: List[ApplicantResponse]
    documents: List[PgsqlDocumentResponse]

    class Config:
        orm_mode = True
