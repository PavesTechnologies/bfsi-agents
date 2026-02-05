"""USPS enrichment API routes."""
from fastapi import APIRouter
from src.api.v1.schemas.enrichment import (
    USPSAddressRequestSchema,
    USPSAddressResponseSchema,
)
from src.services.enrichment_service import EnrichmentService

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post(
    "/usps",
    response_model=USPSAddressResponseSchema,
    summary="Verify Address with USPS Mock",
    description="Verify a US address using mock USPS adapter. Returns address deliverability and ZIP+4.",
)
def verify_address(request: USPSAddressRequestSchema) -> USPSAddressResponseSchema:
    """Verify address with USPS mock adapter.
    
    Args:
        request: Address to verify (address_line1 required)
        
    Returns:
        Address verification result with deliverable status
    """
    return EnrichmentService.verify_address(request)
