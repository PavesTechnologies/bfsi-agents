"""Email enrichment API schemas."""
from typing import Literal
from pydantic import BaseModel, Field


class EmailRequestSchema(BaseModel):
    """Request schema for email domain risk analysis."""
    email: str = Field(..., description="Email address to analyze")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@gmail.com"
            }
        }


class EmailResponseSchema(BaseModel):
    """Response schema for email domain risk analysis."""
    domain: str = Field(..., description="Extracted domain from email")
    risk: Literal["low", "medium", "high"] = Field(..., description="Risk level of domain")
    disposable: bool = Field(..., description="Whether email uses disposable service")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "gmail.com",
                "risk": "low",
                "disposable": False,
                "confidence": 0.95
            }
        }
