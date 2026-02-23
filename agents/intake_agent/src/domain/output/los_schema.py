"""
LOS (Loan Origination System) Schema Definitions

Strict Pydantic models defining the canonical output contract.
These models enforce schema compliance and reject unknown fields.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Application Schema
# ============================================================================

class ApplicationSchema(BaseModel):
    """Schema for loan application data."""

    model_config = ConfigDict(extra="forbid")

    application_id: str = Field(
        ..., description="Unique application identifier"
    )
    loan_type: str = Field(..., description="Type of loan")
    credit_type: Optional[str] = Field(
        default=None, description="Type of credit"
    )
    loan_purpose: Optional[str] = Field(
        default=None, description="Purpose of the loan"
    )
    requested_amount: Optional[float] = Field(
        default=None, description="Requested loan amount"
    )
    requested_term_months: Optional[int] = Field(
        default=None, description="Requested loan term in months"
    )
    preferred_payment_day: Optional[int] = Field(
        default=None, description="Preferred payment day"
    )
    origination_channel: Optional[str] = Field(
        default=None, description="Channel through which application originated"
    )
    application_status: Optional[str] = Field(
        default=None, description="Current status of application"
    )


# ============================================================================
# Applicant Schema
# ============================================================================

class ApplicantSchema(BaseModel):
    """Schema for applicant data."""

    model_config = ConfigDict(extra="forbid")

    applicant_id: str = Field(
        ..., description="Unique applicant identifier"
    )
    applicant_role: str = Field(
        ..., description="Role of applicant (PRIMARY, CO-APPLICANT, etc.)"
    )
    first_name: str = Field(..., description="Applicant first name")
    middle_name: Optional[str] = Field(
        default=None, description="Applicant middle name"
    )
    last_name: str = Field(..., description="Applicant last name")
    suffix: Optional[str] = Field(
        default=None, description="Name suffix (Jr., Sr., III, etc.)"
    )
    date_of_birth: Optional[str] = Field(
        default=None, description="Date of birth (YYYY-MM-DD format)"
    )
    ssn_last4: Optional[str] = Field(
        default=None, description="Last 4 digits of SSN"
    )
    itin_number: Optional[str] = Field(
        default=None, description="ITIN number if applicable"
    )
    citizenship_status: Optional[str] = Field(
        default=None, description="Citizenship status"
    )
    email: Optional[str] = Field(
        default=None, description="Email address"
    )
    phone_number: Optional[str] = Field(
        default=None, description="Phone number"
    )
    gender: Optional[str] = Field(
        default=None, description="Gender"
    )


# ============================================================================
# Evidence Schema
# ============================================================================

class EvidenceSchema(BaseModel):
    """
    Schema for evidence reference data.
    
    Supports traceability fields for linking validation/enrichment
    outputs back to source evidence.
    """

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., description="Path to evidence file")
    type: str = Field(..., description="Type of evidence")
    
    # Traceability fields (optional)
    id: Optional[str] = Field(
        default=None, description="Unique evidence identifier"
    )
    source: Optional[str] = Field(
        default=None, description="Name of validator/adapter that produced this"
    )
    created_at: Optional[str] = Field(
        default=None, description="ISO-8601 timestamp when evidence was recorded"
    )
    entity_type: Optional[str] = Field(
        default=None, description="Type of entity this evidence applies to"
    )
    entity_id: Optional[str] = Field(
        default=None, description="ID of the entity this evidence applies to"
    )
    rule_id: Optional[str] = Field(
        default=None, description="ID of the rule/adapter that validated this"
    )


# ============================================================================
# Enrichments Schema
# ============================================================================

class EnrichmentsSchema(BaseModel):
    """Schema for enrichment data."""

    model_config = ConfigDict(extra="forbid")

    # Enrichments is a flexible dict but still type-checked
    # Each value should be serializable to JSON
    # No explicit field definitions since enrichments are dynamic


# ============================================================================
# Main LOS Output Schema
# ============================================================================

class LOSOutput(BaseModel):
    """
    Canonical output schema for LOS (Loan Origination System) consumption.

    This schema enforces strict compliance with the LOS contract.
    Unknown fields are rejected (extra="forbid").
    All required fields must be present.
    """

    model_config = ConfigDict(extra="forbid")

    application: ApplicationSchema = Field(
        ..., description="Loan application details"
    )
    applicants: List[ApplicantSchema] = Field(
        ..., description="List of applicants (sorted by ID)"
    )
    enrichments: Dict[str, Any] = Field(
        ..., description="Enrichment data keyed by type"
    )
    evidence: List[EvidenceSchema] = Field(
        ..., description="Evidence references (sorted by path)"
    )
    generated_at: str = Field(
        ..., description="ISO-8601 timestamp when output was generated"
    )
