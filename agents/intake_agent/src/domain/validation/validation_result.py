from dataclasses import dataclass

from .reason_codes import ValidationReasonCode


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    reason_code: ValidationReasonCode | None
    message: str | None = None

    @staticmethod
    def success():
        return ValidationResult(True, None, None)

    @staticmethod
    def failure(code: ValidationReasonCode, message: str):
        return ValidationResult(False, code, message)
