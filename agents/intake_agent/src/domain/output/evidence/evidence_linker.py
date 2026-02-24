"""
Evidence Linker

Deterministic linking of evidence references into canonical output.
Maintains traceability without mutating inputs.
"""

from copy import deepcopy
from typing import Any

from src.domain.output.evidence.evidence_models import EvidenceReference


def link_evidence_to_output(
    *,
    canonical_output: dict[str, Any],
    evidence_refs: list[EvidenceReference],
) -> dict[str, Any]:
    """
    Link evidence references into canonical output while preserving immutability.

    This function:
    - Integrates evidence metadata into the canonical output
    - Removes duplicate evidence (by id)
    - Sorts evidence deterministically (type → source → id)
    - Preserves all original output data
    - Does NOT mutate input parameters
    - Does NOT validate LOS schema
    - Does NOT persist evidence
    - Does NOT generate timestamps

    Args:
        canonical_output: Output from assemble_canonical_output()
        evidence_refs: List of EvidenceReference objects

    Returns:
        dict: Canonical output with linked evidence in "evidence" section

    Side Effects:
        None (pure function)
    """

    # Create deep copy to preserve input immutability
    output = deepcopy(canonical_output)

    # Deduplicate evidence by ID
    seen_ids: set[str] = set()
    unique_evidence: list[EvidenceReference] = []

    for evidence in evidence_refs:
        if evidence.id not in seen_ids:
            unique_evidence.append(evidence)
            seen_ids.add(evidence.id)

    # Sort evidence deterministically: type → source → id
    sorted_evidence = sorted(unique_evidence, key=lambda e: e.get_sort_key())

    # Convert evidence references to dicts and filter out None values
    evidence_dicts = []
    for evidence in sorted_evidence:
        evidence_dict = evidence.to_dict()
        # Remove None values to keep output clean
        evidence_dicts.append({k: v for k, v in evidence_dict.items() if v is not None})

    # Update the evidence section in output
    # Merge with any existing evidence, preserving originals if no conflict
    existing_evidence = output.get("evidence", [])

    # Build merged evidence list, preferring new evidence dicts over existing
    existing_by_path = {e.get("path"): e for e in existing_evidence}  # noqa: F841
    merged_evidence = list(evidence_dicts)

    # Add existing evidence that's not in new evidence
    for existing in existing_evidence:
        path = existing.get("path")
        if path and not any(e.get("path") == path for e in merged_evidence):
            merged_evidence.append(existing)

    # Final sort by path for determinism
    output["evidence"] = sorted(merged_evidence, key=lambda e: e.get("path", ""))

    return output


def deduplicate_evidence(
    evidence_refs: list[EvidenceReference],
) -> list[EvidenceReference]:
    """
    Deduplicate evidence references by ID.

    Args:
        evidence_refs: List of EvidenceReference objects

    Returns:
        list: List of unique EvidenceReference objects (by id)
    """
    seen_ids: set[str] = set()
    unique: list[EvidenceReference] = []

    for evidence in evidence_refs:
        if evidence.id not in seen_ids:
            unique.append(evidence)
            seen_ids.add(evidence.id)

    return unique


def sort_evidence(
    evidence_refs: list[EvidenceReference],
) -> list[EvidenceReference]:
    """
    Sort evidence deterministically by type, source, and id.

    Args:
        evidence_refs: List of EvidenceReference objects

    Returns:
        list: Sorted list of EvidenceReference objects
    """
    return sorted(evidence_refs, key=lambda e: e.get_sort_key())


def get_evidence_by_type(
    evidence_refs: list[EvidenceReference],
    evidence_type: str,
) -> list[EvidenceReference]:
    """
    Filter evidence references by type.

    Args:
        evidence_refs: List of EvidenceReference objects
        evidence_type: Type to filter by (validation, enrichment, etc.)

    Returns:
        list: EvidenceReference objects matching the type
    """
    return [e for e in evidence_refs if e.type == evidence_type]


def get_evidence_by_entity(
    evidence_refs: list[EvidenceReference],
    entity_type: str,
    entity_id: str,
) -> list[EvidenceReference]:
    """
    Filter evidence references by entity type and id.

    Args:
        evidence_refs: List of EvidenceReference objects
        entity_type: Entity type to filter by (applicant, address, etc.)
        entity_id: Entity ID to filter by

    Returns:
        list: EvidenceReference objects matching the entity
    """
    return [
        e
        for e in evidence_refs
        if e.entity_type == entity_type and e.entity_id == entity_id
    ]
