"""Phone enrichment API schemas."""
from typing import Optional, Literal
from pydantic import ConfigDict, BaseModel, Field


class PhoneRequestSchema(BaseModel):
    """Request schema for phone intelligence analysis."""
    phone_number: str = Field(..., description="Phone number to analyze (accepts various formats)")

    model_config = ConfigDict(json_schema_extra={"example": {"phone_number": "+1-555-0101000"}})
class PhoneResponseSchema(BaseModel):
    """Response schema for phone intelligence analysis."""
    valid: bool = Field(..., description="Whether the phone number is valid (10+ digits)")
    line_type: Literal["mobile", "landline", "unknown"] = Field(..., description="Type of phone line")
    carrier: Optional[str] = Field(None, description="Carrier information if available")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")

    model_config = ConfigDict(json_schema_extra={"example": {"valid": True, "line_type": "mobile", "carrier": "Mock Carrier", "confidence": 0.92}})