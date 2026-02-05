"""Employer enrichment API routes."""
from fastapi import APIRouter
from src.api.v1.schemas.enrichment import (
    EmployerRequestSchema,
    EmployerResponseSchema,
)
from src.services.enrichment_service import EnrichmentService

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post(
    "/employer",
    response_model=EmployerResponseSchema,
    summary="Verify Employer with Mock",
    description="Verify an employer using mock adapter. Checks for corporate keywords and returns NAICS code.",
)
def verify_employer(request: EmployerRequestSchema) -> EmployerResponseSchema:
    """Verify employer with mock adapter.
    
    Args:
        request: Employer info to verify (employer_name required)
        
    Returns:
        Employer verification result with NAICS code
    """
    return EnrichmentService.verify_employer(request)
