"""
Canonical Output Builder

Pure, deterministic function for assembling final canonical output JSON
for LOS (Loan Origination System) consumption.

Requirements:
- No database access
- No HTTP calls
- No FastAPI imports
- No logging
- No mutation of inputs
- Deterministic output only
"""

from typing import Any, Dict, List, Optional


def _sort_dict_keys(obj: Any) -> Any:
    """
    Recursively sort dictionary keys to ensure deterministic output.
    Preserves lists and other types as-is.
    """
    if isinstance(obj, dict):
        return {k: _sort_dict_keys(obj[k]) for k in sorted(obj.keys())}
    elif isinstance(obj, list):
        return [_sort_dict_keys(item) for item in obj]
    else:
        return obj


def _sort_applicants(applicants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort applicants by stable key for consistent ordering.
    Prefers applicant_id, falls back to role or index.
    """
    if not applicants:
        return []

    def get_sort_key(applicant: Dict[str, Any]) -> tuple:
        # Use applicant_id as primary sort key
        applicant_id = applicant.get("applicant_id")
        if applicant_id is not None:
            return (0, applicant_id)

        # Fall back to applicant_role
        role = applicant.get("applicant_role")
        if role is not None:
            return (1, role)

        # Default stable ordering
        return (2, id(applicant))

    return sorted(applicants, key=get_sort_key)


def _sort_evidence(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort evidence by path for stable ordering.
    """
    if not evidence:
        return []

    def get_sort_key(item: Dict[str, Any]) -> str:
        return item.get("path", "")

    return sorted(evidence, key=get_sort_key)


def assemble_canonical_output(
    *,
    application: Optional[Dict[str, Any]] = None,
    applicants: Optional[List[Dict[str, Any]]] = None,
    enrichments: Optional[Dict[str, Any]] = None,
    evidence_refs: Optional[List[Dict[str, Any]]] = None,
    generated_at: str,
) -> Dict[str, Any]:
    """
    Assemble the final canonical output JSON for LOS consumption.

    This is a pure, deterministic function that:
    - Does NOT access the database
    - Does NOT make HTTP calls
    - Does NOT import FastAPI
    - Does NOT perform logging
    - Does NOT mutate input parameters
    - Returns deterministically ordered output

    Args:
        application: Loan application data (optional)
        applicants: List of applicant records (optional)
        enrichments: Enrichment data keyed by type (optional)
        evidence_refs: List of evidence references (optional)
        generated_at: ISO-8601 timestamp string (required, passed in)

    Returns:
        dict: Canonical output with deterministic ordering:
            {
              "application": { ... },
              "applicants": [ ... ],
              "enrichments": { ... },
              "evidence": [ ... ],
              "generated_at": "ISO-8601"
            }

    Determinism rules:
    - Dictionary keys are sorted alphabetically
    - Applicants sorted by applicant_id, then applicant_role
    - Evidence sorted by path
    - Empty lists used instead of None values
    - Missing optional sections included as empty collections
    """

    # Build output with deterministic structure
    output: Dict[str, Any] = {}

    # Application section
    output["application"] = (
        _sort_dict_keys(application) if application else {}
    )

    # Applicants section - sorted for stability
    sorted_applicants = _sort_applicants(applicants or [])
    output["applicants"] = [
        _sort_dict_keys(app) for app in sorted_applicants
    ]

    # Enrichments section
    output["enrichments"] = (
        _sort_dict_keys(enrichments) if enrichments else {}
    )

    # Evidence section - sorted by path for stability
    sorted_evidence = _sort_evidence(evidence_refs or [])
    output["evidence"] = [
        _sort_dict_keys(ev) for ev in sorted_evidence
    ]

    # Generated timestamp (passed in, not generated here)
    output["generated_at"] = generated_at

    # Final deterministic sort of all top-level keys
    return _sort_dict_keys(output)
