# src/schemas/kyc_request.py

import re
from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator


class Address(BaseModel):
    line1: str
    line2: str | None
    city: str
    state: str
    zip: str


class KYCTriggerRequest(BaseModel):
    applicant_id: str
    full_name: str
    dob: date
    ssn: str = Field(..., min_length=9, max_length=9)
    address: Address
    phone: str
    email: EmailStr
    idempotency_key: str = Field(..., description="Unique key to ensure idempotency of the request")
    selfie_image: str | None = Field(None, description="Base64 encoded selfie image")
    id_card_image: str | None = Field(None, description="Base64 encoded ID card image")

    @field_validator("ssn")
    @classmethod
    def validate_ssn(cls, v):
        if not re.fullmatch(r"\d{9}", v):
            raise ValueError("SSN must be exactly 9 digits")
        return v
