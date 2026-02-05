"""Email enrichment API routes."""
from fastapi import APIRouter
from src.api.v1.schemas.enrichment import (
    EmailRequestSchema,
    EmailResponseSchema,
)
from src.services.enrichment_service import EnrichmentService

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post(
    "/email",
    response_model=EmailResponseSchema,
    summary="Analyze Email Domain with Mock",
    description="Analyze an email domain using mock adapter. Classifies risk level and detects disposable domains.",
)
def analyze_email_domain(request: EmailRequestSchema) -> EmailResponseSchema:
    """Analyze email domain with mock adapter.
    
    Args:
        request: Email to analyze (email required)
        
    Returns:
        Email risk result with domain risk classification
    """
    return EnrichmentService.analyze_email_domain(request)
