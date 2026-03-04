"""
Evidence Models for Traceability

Immutable contracts for evidence references.
Metadata only - no raw evidence data stored here.
"""

from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime


EvidenceType = Literal[
    "validation",
    "enrichment",
    "document",
    "verification",
]


@dataclass(frozen=True)
class EvidenceReference:
    """
    Immutable evidence reference linking validation/enrichment outputs
    to physical evidence artifacts.

    Attributes:
        id: Unique evidence identifier
        type: Category of evidence (validation, enrichment, document, verification)
        source: Name of validator/adapter that produced this reference
        path: Path to evidence (filesystem, object store, etc.)
        created_at: ISO-8601 timestamp when evidence was recorded
        entity_type: Type of entity this evidence applies to (optional)
                    (applicant, address, employment, enrichment)
        entity_id: ID of the entity this evidence applies to (optional)
        rule_id: ID of the rule/adapter that validated this (optional)
    """

    id: str
    type: EvidenceType
    source: str
    path: str
    created_at: str

    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    rule_id: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for inclusion in canonical output.

        Returns:
            dict: Evidence reference as JSON-serializable dict
        """
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "path": self.path,
            "created_at": self.created_at,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "rule_id": self.rule_id,
        }

    def get_sort_key(self) -> tuple:
        """
        Get deterministic sort key for ordering evidence.

        Returns:
            tuple: (type, source, id) for stable ordering
        """
        return (self.type, self.source, self.id)
