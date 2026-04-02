"""Types for normalized underwriting audit narratives."""

from typing import Any, Dict, List, TypedDict


class UnderwritingAuditNarrative(TypedDict):
    application_id: str
    decision: str
    policy_id: str | None
    policy_version: str | None
    model_version: str | None
    prompt_version: str | None
    risk_tier: str | None
    risk_score: float | None
    requested_amount: float
    requested_tenure_months: int
    key_factors: List[str]
    triggered_reason_keys: List[str]
    candidate_reason_codes: List[Dict[str, Any]]
    selected_reason_codes: List[Dict[str, Any]]
    policy_citations: List[Dict[str, Any]]
    retrieval_evidence: List[Dict[str, Any]]
    feature_attribution_summary: Dict[str, Any]
    calculations: Dict[str, Any]
    decision_path: List[str]
    human_review_required: bool
    human_review_outcome: str | None
    routing: Dict[str, Any]
