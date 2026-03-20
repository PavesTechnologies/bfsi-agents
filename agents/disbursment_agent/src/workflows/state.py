"""
Workflow state for the disbursement graph.
"""

from typing import Any, Dict, List, Optional, TypedDict


class DisbursementState(TypedDict, total=False):
    application_id: str
    decision: str
    risk_tier: Optional[str]
    risk_score: Optional[float]

    approved_amount: Optional[float]
    approved_tenure_months: Optional[int]
    interest_rate: Optional[float]
    disbursement_amount: Optional[float]

    counter_offer: Optional[Dict[str, Any]]
    selected_option_id: Optional[str]
    explanation: Optional[str]

    disbursement_status: str
    validation_passed: Optional[bool]

    monthly_emi: Optional[float]
    total_interest: Optional[float]
    total_repayment: Optional[float]
    first_emi_date: Optional[str]
    repayment_schedule: Optional[List[Dict[str, Any]]]

    transaction_id: Optional[str]
    transfer_status: Optional[str]
    transfer_timestamp: Optional[str]
    reconciliation_required: Optional[bool]
    gateway_response: Optional[Dict[str, Any]]

    disbursement_receipt: Optional[Dict[str, Any]]
    error: Optional[str]
