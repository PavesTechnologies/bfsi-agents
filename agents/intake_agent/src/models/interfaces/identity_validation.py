from pydantic import BaseModel
from typing import Any, List


class FieldMismatch(BaseModel):
    field: str
    expected: Any
    actual: Any


class CrossValidationResult(BaseModel):
    valid: bool
    mismatches: List[FieldMismatch]
