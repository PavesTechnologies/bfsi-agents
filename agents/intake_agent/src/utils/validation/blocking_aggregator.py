"""Blocking validation aggregator for loan intake.

Provides complete validation for applicant, address, and employment fields
with all errors collected upfront. Validation errors block any database
operations and return all issues in a single HTTP 400 response.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.domain.validation.reason_codes import ValidationReasonCode
from src.domain.validation.typed_field_validators import (
    validate_first_name,
    validate_last_name,
    validate_ssn_last4,
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
)


@dataclass
class ValidationError:
    """Represents a single validation error."""
    field: str
    message: str
    reason_code: ValidationReasonCode = None  


@dataclass
class BlockingValidationSummary:
    """Summary of blocking validation results."""
    is_valid: bool
    errors: List[ValidationError]
    
    def to_http_detail(self) -> List[Dict[str, str]]:
        """Convert errors to HTTP 400 detail format."""
        return [{"field": error.field, "message": error.message, "reason_code": error.reason_code.value} for error in self.errors]


# def validate_applicant_blocking(applicant) -> BlockingValidationSummary:
#     """Validate applicant fields and return all errors at once.
    
#     Returns:
#         BlockingValidationSummary with is_valid=True if all validations pass,
#         False otherwise. All validation errors are collected in the errors list.
#     """
#     errors: List[ValidationError] = []
    
#     # ==================== Applicant Fields ====================
#     # First Name
#     first_name = getattr(applicant, "first_name", None)
#     result = validate_first_name(first_name)
#     if not result.passed:
#         errors.append(ValidationError(field="applicant.first_name", message=result.message, reason_code=result.reason_code))
    
#     # Last Name
#     last_name = getattr(applicant, "last_name", None)
#     result = validate_last_name(last_name)
#     if not result.passed:
#         errors.append(ValidationError(field="applicant.last_name", message=result.message, reason_code=result.reason_code))
    
#     # SSN Last 4
#     ssn_last4 = getattr(applicant, "ssn_last4", None)
#     result = validate_ssn_last4(ssn_last4)
#     if not result.passed:
#         errors.append(ValidationError(field="applicant.ssn_last4", message=result.message, reason_code=result.reason_code))
    
#     # Date of Birth
#     dob = getattr(applicant, "date_of_birth", None)
#     result = validate_dob(dob)
#     if not result.passed:
#         errors.append(ValidationError(field="applicant.date_of_birth", message=result.message, reason_code=result.reason_code))
    
#     # Email
#     email = getattr(applicant, "email", None)
#     result = validate_email(email)
#     if not result.passed:
#         errors.append(ValidationError(field="applicant.email", message=result.message, reason_code=result.reason_code))
    
#     # ==================== Address Fields ====================
#     addresses = getattr(applicant, "addresses", []) or []
#     for idx, address in enumerate(addresses):
#         # Address Line 1
#         address_line1 = getattr(address, "address_line1", None)
#         result = validate_address_line(address_line1)
#         if not result.passed:
#             errors.append(ValidationError(
#                 field=f"address[{idx}].address_line1",
#                 message=result.message,
#                 reason_code=result.reason_code
#             ))
        
#         # City
#         city = getattr(address, "city", None)
#         result = validate_city(city)
#         if not result.passed:
#             errors.append(ValidationError(
#                 field=f"address[{idx}].city",
#                 message=result.message,
#                 reason_code=result.reason_code
#             ))
        
#         # State
#         state = getattr(address, "state", None)
#         result = validate_state(state)
#         if not result.passed:
#             errors.append(ValidationError(
#                 field=f"address[{idx}].state",
#                 message=result.message,
#                 reason_code=result.reason_code
#             ))
        
#         # ZIP Code
#         zip_code = getattr(address, "zip_code", None)
#         result = validate_zip(zip_code)
#         if not result.passed:
#             errors.append(ValidationError(
#                 field=f"address[{idx}].zip_code",
#                 message=result.message,
#                 reason_code=result.reason_code
#             ))
    
#     # ==================== Employment Fields ====================
#     employment = getattr(applicant, "employment", None)
#     if employment:
#         # Employment Type
#         employment_type = getattr(employment, "employment_type", None)
#         result = validate_employment_type(employment_type)
#         if not result.passed:
#             errors.append(ValidationError(
#                 field="employment.employment_type",
#                 message=result.message,
#                 reason_code=result.reason_code
#             ))
        
#         # Employer Name
#         employer_name = getattr(employment, "employer_name", None)
#         result = validate_employer_name(employer_name)
#         if not result.passed:
#             errors.append(ValidationError(
#                 field="employment.employer_name",
#                 message=result.message,
#                 reason_code=result.reason_code
#             ))
        
#         # Job Title
#         job_title = getattr(employment, "job_title", None)
#         result = validate_job_title(job_title)
#         if not result.passed:
#             errors.append(ValidationError(
#                 field="employment.job_title",
#                 message=result.message,
#                 reason_code=result.reason_code
#             ))
        
#         # Gross Monthly Income
#         gross_monthly_income = getattr(employment, "gross_monthly_income", None)
#         result = validate_monthly_income(gross_monthly_income)
#         if not result.passed:
#             errors.append(ValidationError(
#                 field="employment.gross_monthly_income",
#                 message=result.message,
#                 reason_code=result.reason_code
#             ))
    
#     is_valid = len(errors) == 0
#     return BlockingValidationSummary(is_valid=is_valid, errors=errors)


## New Version DRY
def validate_applicant_blocking(applicant) -> BlockingValidationSummary:
    errors: List[ValidationError] = []

    # 1. Define validation map for simple fields
    validation_map = [
        ("applicant.first_name", getattr(applicant, "first_name", None), validate_first_name),
        ("applicant.last_name", getattr(applicant, "last_name", None), validate_last_name),
        ("applicant.ssn_last4", getattr(applicant, "ssn_last4", None), validate_ssn_last4),
        ("applicant.date_of_birth", getattr(applicant, "date_of_birth", None), validate_dob),
        ("applicant.email", getattr(applicant, "email", None), validate_email),
    ]

    # 2. Execute Simple Fields
    for field_path, value, validator in validation_map:
        result = validator(value)
        if not result.passed:
            errors.append(ValidationError(
                field=field_path, 
                message=result.message, 
                reason_code=result.reason_code
            ))

    # 3. Handle Nested Collections (Addresses)
    for idx, addr in enumerate(getattr(applicant, "addresses", []) or []):
        addr_map = [
            (f"address[{idx}].address_line1", getattr(addr, "address_line1", None), validate_address_line),
            (f"address[{idx}].city", getattr(addr, "city", None), validate_city),
            (f"address[{idx}].state", getattr(addr, "state", None), validate_state),
            (f"address[{idx}].zip_code", getattr(addr, "zip_code", None), validate_zip),
        ]
        for path, val, validator in addr_map:
            res = validator(val)
            if not res.passed:
                errors.append(ValidationError(field=path, message=res.message, reason_code=res.reason_code))

    # 4. Handle Optional Nested Objects (Employment)
    emp = getattr(applicant, "employment", None)
    if emp:
        emp_map = [
            ("employment.type", getattr(emp, "employment_type", None), validate_employment_type),
            ("employment.employer", getattr(emp, "employer_name", None), validate_employer_name),
            ("employment.income", getattr(emp, "gross_monthly_income", None), validate_monthly_income),
        ]
        for path, val, validator in emp_map:
            res = validator(val)
            if not res.passed:
                errors.append(ValidationError(field=path, message=res.message, reason_code=res.reason_code))

    return BlockingValidationSummary(is_valid=len(errors) == 0, errors=errors)


def validate_all_applicants_blocking(applicants: List[Any]) -> BlockingValidationSummary:
    """Validate all applicants and collect all errors at once.
    
    Returns:
        BlockingValidationSummary with is_valid=True only if ALL applicants
        and their nested fields pass validation. All errors across all applicants
        are collected together.
    """
    all_errors: List[ValidationError] = []
    
    for idx, applicant in enumerate(applicants):
        summary = validate_applicant_blocking(applicant)
        if not summary.is_valid:
            for error in summary.errors:
                # Prefix with applicant index for clarity
                field = f"applicants[{idx}].{error.field}"
                all_errors.append(ValidationError(field=field, message=error.message , reason_code=error.reason_code))
    
    is_valid = len(all_errors) == 0
    return BlockingValidationSummary(is_valid=is_valid, errors=all_errors)
