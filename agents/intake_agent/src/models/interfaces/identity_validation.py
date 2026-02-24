from typing import Any

from pydantic import BaseModel


class FieldMismatch(BaseModel):
    field: str
    expected: Any
    actual: Any


class CrossValidationResult(BaseModel):
    valid: bool
    mismatches: list[FieldMismatch]
