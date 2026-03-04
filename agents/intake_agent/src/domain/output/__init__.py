"""Output module for canonical JSON assembly, LOS schema validation, and evidence linking."""

from src.domain.output.canonical_builder import assemble_canonical_output
from src.domain.output.los_schema import (
    ApplicationSchema,
    ApplicantSchema,
    EvidenceSchema,
    EnrichmentsSchema,
    LOSOutput,
)
from src.domain.output.schema_validator import (
    validate_los_output,
    LOSSchemaValidationError,
)
from src.domain.output.evidence import (
    EvidenceReference,
    EvidenceType,
    link_evidence_to_output,
    deduplicate_evidence,
    sort_evidence,
    get_evidence_by_type,
    get_evidence_by_entity,
)

__all__ = [
    "assemble_canonical_output",
    "ApplicationSchema",
    "ApplicantSchema",
    "EvidenceSchema",
    "EnrichmentsSchema",
    "LOSOutput",
    "validate_los_output",
    "LOSSchemaValidationError",
    "EvidenceReference",
    "EvidenceType",
    "link_evidence_to_output",
    "deduplicate_evidence",
    "sort_evidence",
    "get_evidence_by_type",
    "get_evidence_by_entity",
]
