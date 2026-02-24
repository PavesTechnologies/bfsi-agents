from __future__ import annotations

import datetime
import uuid

from pydantic import AnyUrl, BaseModel, Field


class EmploymentInfo(BaseModel):
    """Employment details for an applicant.

    This model contains pure, structural fields only and is intended to be
    extended with domain-specific validation in a separate layer.
    """

    employment_type: str = Field(
        ..., description="Type of employment (e.g., full-time, part-time, contract)"
    )
    employment_status: str = Field(
        ..., description="Current employment status (e.g., active, inactive)"
    )
    employer_name: str = Field(..., description="Name of the employer")
    employer_phone: str = Field(..., description="Employer phone number")
    job_title: str = Field(..., description="Job title or position held")
    start_date: datetime.date = Field(..., description="Employment start date")
    gross_monthly_income: float = Field(
        ..., description="Gross monthly income in local currency"
    )
    self_employed_flag: bool = Field(
        ..., description="True if the applicant is self-employed"
    )


class ApplicantInfo(BaseModel):
    """Applicant identity and contact information."""

    applicant_role: str = Field(
        ..., description="Role of applicant in the loan (e.g., primary, co-applicant)"
    )
    first_name: str = Field(..., description="Applicant's first name")
    middle_name: str | None = Field(None, description="Applicant's middle name, if any")
    last_name: str = Field(..., description="Applicant's last name")
    date_of_birth: datetime.date = Field(..., description="Applicant's date of birth")
    ssn_last4: str | None = Field(None, description="Last 4 digits of SSN, if provided")
    itin_number: str | None = Field(None, description="ITIN number, if provided")
    citizenship_status: str = Field(
        ..., description="Citizenship status (e.g., citizen, resident)"
    )
    email: str = Field(..., description="Applicant's contact email address")
    employment: EmploymentInfo = Field(
        ..., description="Applicant's employment information"
    )


class LoanIntakeRequest(BaseModel):
    """Top-level loan intake request model for submission endpoint."""

    request_id: uuid.UUID = Field(
        ..., description="Unique identifier for the intake request"
    )
    callback_url: AnyUrl | None = Field(
        None, description="Optional callback URL to receive updates"
    )
    app_id: uuid.UUID = Field(..., description="Application identifier")
    loan_type: str = Field(
        ..., description="Type of loan requested (e.g., mortgage, personal)"
    )
    credit_type: str = Field(..., description="Type of credit or credit product")
    requested_amount: float = Field(..., description="Requested loan amount")
    requested_term_months: int = Field(..., description="Requested loan term in months")
    application_status: str = Field(
        ..., description="Current status of the application"
    )
    applicants: list[ApplicantInfo] = Field(
        ..., description="List of applicants associated with this request"
    )
