"""Employer enrichment API schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class EmployerRequestSchema(BaseModel):
    """Request schema for employer verification."""
    employer_name: str = Field(..., description="Company or business name")
    state: Optional[str] = Field(None, description="State of operation")
    naics_code: Optional[str] = Field(None, description="NAICS industry code")

    class Config:
        json_schema_extra = {
            "example": {
                "employer_name": "Acme Corporation Inc",
                "state": "CA",
                "naics_code": "541512"
            }
        }


class EmployerResponseSchema(BaseModel):
    """Response schema for employer verification."""
    verified: bool = Field(..., description="Whether employer was verified")
    naics_code: Optional[str] = Field(None, description="NAICS code assigned")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")

    class Config:
        json_schema_extra = {
            "example": {
                "verified": True,
                "naics_code": "541512",
                "confidence": 0.85
            }
        }
