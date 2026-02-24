"""Output module for canonical JSON assembly, \
    LOS schema validation, and evidence linking."""

from src.domain.output.canonical_builder import assemble_canonical_output
from src.domain.output.evidence import (
    EvidenceReference,
    EvidenceType,
    deduplicate_evidence,
    get_evidence_by_entity,
    get_evidence_by_type,
    link_evidence_to_output,
    sort_evidence,
)
from src.domain.output.los_schema import (
    ApplicantSchema,
    ApplicationSchema,
    EnrichmentsSchema,
    EvidenceSchema,
    LOSOutput,
)
from src.domain.output.schema_validator import (
    LOSSchemaValidationError,
    validate_los_output,
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
