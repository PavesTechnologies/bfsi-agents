"""Blocking validation aggregator for loan intake.

Provides complete validation for applicant, address, and employment fields
with all errors collected upfront. Validation errors block any database
operations and return all issues in a single HTTP 400 response.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.domain.validation.typed_field_validators import (
    validate_first_name,
    validate_last_name,
    validate_ssn_last4,
    validate_ssn,
    validate_dob,
    validate_email,
    validate_address_line,
    validate_city,
    validate_state,
    validate_zip,
    validate_employment_type,
    validate_employer_name,
    validate_job_title,
    validate_monthly_income,
    validate_requested_amount,
    validate_requested_term,
)


@dataclass
class ValidationError:
    """Represents a single validation error."""
    field: str
    message: str


@dataclass
class BlockingValidationSummary:
    """Summary of blocking validation results."""
    is_valid: bool
    errors: List[ValidationError]
    
    def to_http_detail(self) -> List[Dict[str, str]]:
        """Convert errors to HTTP 400 detail format."""
        return [{"field": error.field, "message": error.message} for error in self.errors]

    def model_dump(self) -> Dict[str, Any]:
        """Dump to dict for compatibility with Pydantic usage."""
        return {
            "is_valid": self.is_valid,
            "errors": [{"field": e.field, "message": e.message} for e in self.errors]
        }


def validate_applicant_blocking(applicant) -> BlockingValidationSummary:
    """Validate applicant fields and return all errors at once.
    
    Returns:
        BlockingValidationSummary with is_valid=True if all validations pass,
        False otherwise. All validation errors are collected in the errors list.
    """
    errors: List[ValidationError] = []
    
    errors: List[ValidationError] = []
    
    # ==================== Applicant Fields ====================

    # First Name
    first_name = getattr(applicant, "first_name", None)
    result = validate_first_name(first_name)
    if not result.passed:
        errors.append(ValidationError(field="applicant.first_name", message=result.message))
    
    # Last Name
    last_name = getattr(applicant, "last_name", None)
    result = validate_last_name(last_name)
    if not result.passed:
        errors.append(ValidationError(field="applicant.last_name", message=result.message))
    
    # SSN Last 4
    ssn_last4 = getattr(applicant, "ssn_last4", None)
    result = validate_ssn_last4(ssn_last4)
    if not result.passed:
        errors.append(ValidationError(field="applicant.ssn_last4", message=result.message))

    # SSN Full (New Addition)
    ssn_no = getattr(applicant, "ssn_no", None)
    if ssn_no:
        result = validate_ssn(ssn_no)
        if not result.passed:
            errors.append(ValidationError(field="applicant.ssn_no", message=result.message))
    
    # Date of birth
    dob = getattr(applicant, "date_of_birth", None)
    result = validate_dob(dob)
    if not result.passed:
        # 🔹 UNDERAGE IS NON-BLOCKING:
        # We want to record this issue but NOT block the application from being submitted.
        # This allows the application to reach the "non-blocking" validation phase where
        # it will be saved to the database for reviewer visibility.
        from src.domain.validation.reason_codes import ValidationReasonCode
        if result.reason_code != ValidationReasonCode.AGE_BELOW_MINIMUM:
            errors.append(ValidationError(field="applicant.date_of_birth", message=result.message))
    
    # Email (NON-BLOCKING)
    email = getattr(applicant, "email", None)
    result = validate_email(email)
    if not result.passed:
        # 🔹 EMAIL FORMAT IS NON-BLOCKING:
        # We record it but don't stop submission.
        pass
    
    # ==================== Address Fields ====================
    addresses = getattr(applicant, "addresses", []) or []
    for idx, address in enumerate(addresses):
        # Address Line 1
        address_line1 = getattr(address, "address_line1", None)
        result = validate_address_line(address_line1)
        if not result.passed:
            errors.append(ValidationError(
                field=f"address[{idx}].address_line1",
                message=result.message
            ))
        
        # City
        city = getattr(address, "city", None)
        result = validate_city(city)
        if not result.passed:
            errors.append(ValidationError(
                field=f"address[{idx}].city",
                message=result.message
            ))
        
        # State
        state = getattr(address, "state", None)
        result = validate_state(state)
        if not result.passed:
            errors.append(ValidationError(
                field=f"address[{idx}].state",
                message=result.message
            ))
        
        # ZIP Code
        zip_code = getattr(address, "zip_code", None)
        result = validate_zip(zip_code)
        if not result.passed:
            errors.append(ValidationError(
                field=f"address[{idx}].zip_code",
                message=result.message
            ))
    
    # ==================== Employment Fields ====================
    employment = getattr(applicant, "employment", None)
    if employment:
        # Employment Type
        employment_type = getattr(employment, "employment_type", None)
        result = validate_employment_type(employment_type)
        if not result.passed:
            errors.append(ValidationError(
                field="employment.employment_type",
                message=result.message
            ))
        
        # Employer Name
        employer_name = getattr(employment, "employer_name", None)
        result = validate_employer_name(employer_name)
        if not result.passed:
            errors.append(ValidationError(
                field="employment.employer_name",
                message=result.message
            ))
        
        # Job Title
        job_title = getattr(employment, "job_title", None)
        result = validate_job_title(job_title)
        if not result.passed:
            errors.append(ValidationError(
                field="employment.job_title",
                message=result.message
            ))
        
        # Gross Monthly Income
        gross_monthly_income = getattr(employment, "gross_monthly_income", None)
        result = validate_monthly_income(gross_monthly_income)
        if not result.passed:
            errors.append(ValidationError(
                field="employment.gross_monthly_income",
                message=result.message
            ))
    
    is_valid = len(errors) == 0
    return BlockingValidationSummary(is_valid=is_valid, errors=errors)


def validate_loan_blocking(loan) -> BlockingValidationSummary:
    """Validate loan-level fields."""
    errors: List[ValidationError] = []
    
    # Amount
    amount = getattr(loan, "requested_amount", None)
    result = validate_requested_amount(amount)
    if not result.passed:
        errors.append(ValidationError(field="requested_amount", message=result.message))
        
    # Term
    term = getattr(loan, "requested_term_months", None)
    result = validate_requested_term(term)
    if not result.passed:
        errors.append(ValidationError(field="requested_term_months", message=result.message))
        
    is_valid = len(errors) == 0
    return BlockingValidationSummary(is_valid=is_valid, errors=errors)


def validate_all_applicants_blocking(request_body: Any) -> BlockingValidationSummary:
    """Validate entire request including loan level and all applicants.
    
    Returns:
        BlockingValidationSummary with is_valid=True only if everything
        passes structural validation.
    """
    all_errors: List[ValidationError] = []
    
    # 1. Loan Level
    loan_summary = validate_loan_blocking(request_body)
    if not loan_summary.is_valid:
        all_errors.extend(loan_summary.errors)
        
    # 2. Applicants
    applicants = getattr(request_body, "applicants", []) or []
    for idx, applicant in enumerate(applicants):
        summary = validate_applicant_blocking(applicant)
        if not summary.is_valid:
            for error in summary.errors:
                # Prefix with applicant index for clarity
                field = f"applicants[{idx}].{error.field}"
                all_errors.append(ValidationError(field=field, message=error.message))
    
    is_valid = len(all_errors) == 0
    return BlockingValidationSummary(is_valid=is_valid, errors=all_errors)
