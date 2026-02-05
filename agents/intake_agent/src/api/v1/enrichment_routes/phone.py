"""Phone enrichment API routes."""
from fastapi import APIRouter
from src.api.v1.schemas.enrichment import (
    PhoneRequestSchema,
    PhoneResponseSchema,
)
from src.services.enrichment_service import EnrichmentService

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post(
    "/phone",
    response_model=PhoneResponseSchema,
    summary="Analyze Phone Number with Mock",
    description="Analyze a phone number using mock adapter. Validates digit count and returns line type.",
)
def analyze_phone(request: PhoneRequestSchema) -> PhoneResponseSchema:
    """Analyze phone number with mock adapter.
    
    Args:
        request: Phone number to analyze (phone_number required)
        
    Returns:
        Phone intelligence result with validity and line type
    """
    return EnrichmentService.analyze_phone(request)
