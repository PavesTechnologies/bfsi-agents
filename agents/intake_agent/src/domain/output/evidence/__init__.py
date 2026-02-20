"""Evidence linking module for traceability."""

from src.domain.output.evidence.evidence_models import (
    EvidenceReference,
    EvidenceType,
)
from src.domain.output.evidence.evidence_linker import (
    link_evidence_to_output,
    deduplicate_evidence,
    sort_evidence,
    get_evidence_by_type,
    get_evidence_by_entity,
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
