"""Evidence linking module for traceability."""

from src.domain.output.evidence.evidence_linker import (
    deduplicate_evidence,
    get_evidence_by_entity,
    get_evidence_by_type,
    link_evidence_to_output,
    sort_evidence,
)
from src.domain.output.evidence.evidence_models import (
    EvidenceReference,
    EvidenceType,
)

__all__ = [
    "EvidenceReference",
    "EvidenceType",
    "link_evidence_to_output",
    "deduplicate_evidence",
    "sort_evidence",
    "get_evidence_by_type",
    "get_evidence_by_entity",
]
