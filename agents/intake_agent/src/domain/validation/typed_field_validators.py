from datetime import date

from .validation_result import ValidationResult
from .reason_codes import ValidationReasonCode
from .constants import (
    NAME_REGEX,
    EMAIL_REGEX,
    PHONE_REGEX,
    AADHAAR_REGEX,
    AADHAAR_LAST4_REGEX,
    PAN_REGEX,
    PINCODE_REGEX,
    IFSC_REGEX,
    INDIAN_STATE_CODES,
    VOTER_ID_REGEX,
    EMPLOYMENT_TYPES,
)


def validate_first_name(value: str) -> ValidationResult:
    if not value or not NAME_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_FIRST_NAME,
            "First name contains invalid characters"
        )
    return ValidationResult.success()


def validate_last_name(value: str) -> ValidationResult:
    if not value or not NAME_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_LAST_NAME,
            "Last name contains invalid characters"
        )
    return ValidationResult.success()


def validate_aadhaar(value: str) -> ValidationResult:
    if value is None:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_AADHAAR_FORMAT,
            "Aadhaar number is required"
        )
    if not AADHAAR_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_AADHAAR_FORMAT,
            "Aadhaar must be a 12-digit number"
        )
    return ValidationResult.success()


def validate_aadhaar_last4(value: str) -> ValidationResult:
    if value is None:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_AADHAAR_LAST4,
            "Aadhaar last4 is required"
        )
    if not AADHAAR_LAST4_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_AADHAAR_LAST4,
            "Aadhaar last4 must be exactly 4 digits"
        )
    return ValidationResult.success()


def validate_pan(value: str) -> ValidationResult:
    if value is None:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_PAN_FORMAT,
            "PAN number is required"
        )
    if not PAN_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_PAN_FORMAT,
            "PAN must be a standard format like ABCDE1234F"
        )
    return ValidationResult.success()


def validate_voter_id(value: str) -> ValidationResult:
    if value is None:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_VOTER_ID_FORMAT,
            "Voter ID is required"
        )
    if not VOTER_ID_REGEX.match(value.upper()):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_VOTER_ID_FORMAT,
            "Voter ID must be 3 letters followed by 7 digits (e.g. ABC1234567)"
        )
    return ValidationResult.success()


def validate_dob(value: date) -> ValidationResult:
    if value is None:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_DOB_FORMAT,
            "Date of birth is required"
        )
    if value >= date.today():
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_DOB_FORMAT,
            "DOB must be in the past"
        )
    age = date.today().year - value.year - (
        (date.today().month, date.today().day) < (value.month, value.day)
    )
    if age < 18:
        return ValidationResult.failure(
            ValidationReasonCode.AGE_BELOW_MINIMUM,
            "Applicant must be at least 18 years old"
        )
    return ValidationResult.success()


def validate_email(value: str) -> ValidationResult:
    if value is None:
        return ValidationResult.success()
    if not EMAIL_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_EMAIL_FORMAT,
            "Invalid email address format"
        )
    return ValidationResult.success()


def validate_phone(value: str) -> ValidationResult:
    if not PHONE_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_PHONE_FORMAT,
            "Phone must be E.164 India format (+91XXXXXXXXXX, starting with 6-9)"
        )
    return ValidationResult.success()


def validate_address_line(value: str) -> ValidationResult:
    if not value or len(value) < 5:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_ADDRESS_LINE,
            "Address line too short or empty"
        )
    return ValidationResult.success()


def validate_city(value: str) -> ValidationResult:
    if not value or len(value) < 2:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_CITY,
            "City name invalid"
        )
    return ValidationResult.success()


def validate_state(value: str) -> ValidationResult:
    if value.upper() not in INDIAN_STATE_CODES:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_STATE_CODE,
            "Invalid Indian state/UT code"
        )
    return ValidationResult.success()


def validate_pincode(value: str) -> ValidationResult:
    if not PINCODE_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_PINCODE_FORMAT,
            "PIN code must be a 6-digit Indian postal code"
        )
    return ValidationResult.success()


def validate_ifsc(value: str) -> ValidationResult:
    if not IFSC_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_IFSC_FORMAT,
            "IFSC must be 11 characters: 4 letters + 0 + 6 alphanumeric"
        )
    return ValidationResult.success()


def validate_employment_type(value: str) -> ValidationResult:
    if value not in EMPLOYMENT_TYPES:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_EMPLOYMENT_TYPE,
            "Unsupported employment type"
        )
    return ValidationResult.success()


def validate_employer_name(value: str) -> ValidationResult:
    if not value or len(value) < 2:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_EMPLOYER_NAME,
            "Employer name is invalid"
        )
    return ValidationResult.success()


def validate_job_title(value: str) -> ValidationResult:
    if not value or len(value) < 2:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_JOB_TITLE,
            "Job title is invalid"
        )
    return ValidationResult.success()


def validate_monthly_income(value: float) -> ValidationResult:
    if value is None or value <= 0:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_MONTHLY_INCOME,
            "Monthly income must be greater than zero"
        )
    return ValidationResult.success()


def validate_requested_amount(value: float) -> ValidationResult:
    if value is None or value <= 0:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_LOAN_AMOUNT,
            "Requested amount must be greater than zero"
        )
    return ValidationResult.success()


def validate_requested_term(value: int) -> ValidationResult:
    if value is None or value <= 1:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_LOAN_TERM,
            "Requested term must be greater than 1 month"
        )
    return ValidationResult.success()

def validate_zip_code(value: str) -> ValidationResult:
    if not PINCODE_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_ZIP_CODE,
            "ZIP code must be a 6-digit Indian postal code"
        )
    return ValidationResult.success()
