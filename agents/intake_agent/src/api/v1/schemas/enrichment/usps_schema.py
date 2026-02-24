"""USPS enrichment API schemas."""

from pydantic import BaseModel, ConfigDict, Field


class USPSAddressRequestSchema(BaseModel):
    """Request schema for USPS address verification."""

    address_line1: str = Field(..., description="Primary address line")
    address_line2: str | None = Field(
        None, description="Secondary address line (apt, suite, etc)"
    )
    city: str | None = Field(None, description="City name")
    state: str | None = Field(None, description="State code (e.g., CA, NY)")
    zip_code: str | None = Field(None, description="ZIP code")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "address_line1": "123 Main St",
                "address_line2": "Apt 4B",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94102",
            }
        }
    )


class USPSAddressResponseSchema(BaseModel):
    """Response schema for USPS address verification."""

    deliverable: bool = Field(..., description="Whether the address is deliverable")
    standardized_address: str | None = Field(
        None, description="Standardized address format"
    )
    zip5: str | None = Field(None, description="5-digit ZIP code")
    zip4: str | None = Field(None, description="ZIP+4 extension")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deliverable": True,
                "standardized_address": "123 MAIN ST APT 4B",
                "zip5": "94102",
                "zip4": "1234",
                "confidence": 0.9,
            }
        }
    )
