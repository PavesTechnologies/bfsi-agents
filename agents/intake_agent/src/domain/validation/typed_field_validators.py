from .validation_result import ValidationResult
from .reason_codes import ValidationReasonCode
from .constants import NAME_REGEX


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
from .constants import SSN_REGEX, SSN_LAST4_REGEX


def validate_ssn(value: str) -> ValidationResult:
    if not SSN_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_SSN_FORMAT,
            "SSN must follow AAA-GG-SSSS format"
        )
    return ValidationResult.success()


def validate_ssn_last4(value: str) -> ValidationResult:
    if not SSN_LAST4_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_SSN_LAST4,
            "SSN last4 must be exactly 4 digits"
        )
    return ValidationResult.success()
from datetime import date


def validate_dob(value: date) -> ValidationResult:
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
from .constants import EMAIL_REGEX, PHONE_REGEX


def validate_email(value: str) -> ValidationResult:
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
            "Phone must be E.164 US format (+1XXXXXXXXXX)"
        )
    return ValidationResult.success()
from .constants import ZIP_REGEX, STATE_CODES


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
    if value not in STATE_CODES:
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_STATE_CODE,
            "Invalid US state code"
        )
    return ValidationResult.success()


def validate_zip(value: str) -> ValidationResult:
    if not ZIP_REGEX.match(value):
        return ValidationResult.failure(
            ValidationReasonCode.INVALID_ZIP_FORMAT,
            "ZIP must be 5 or 9 digits"
        )
    return ValidationResult.success()
from .constants import EMPLOYMENT_TYPES


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
