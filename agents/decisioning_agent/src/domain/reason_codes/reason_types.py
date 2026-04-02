"""Typed reason-code contracts for adverse-action and review packaging."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ReasonDefinition(BaseModel):
    reason_key: str
    reason_code: str
    official_text: str
    priority: int
    trigger_logic: str
    applicable_products: List[str]


class ReasonTriggerResult(BaseModel):
    reason_key: str
    reason_code: str
    official_text: str
    trigger_source: str
    metric_name: str
    metric_value: Any
    threshold_value: Any
    severity: str
    applicable_product: str
    citation_reference: Optional[str] = None
    internal_rationale: Optional[str] = None


class DisclosureTemplate(BaseModel):
    reason_key: str
    notice_text: str
    reviewer_text: str
    internal_text: str


class ReasonSelectionContext(BaseModel):
    product_code: str
    aggregated_risk_tier: str
    public_record_data: Dict[str, Any]
    income_data: Dict[str, Any]
    behavior_data: Dict[str, Any]
    utilization_data: Dict[str, Any]
    exposure_data: Dict[str, Any]
    inquiry_data: Dict[str, Any]
    credit_score_data: Optional[Dict[str, Any]] = None
