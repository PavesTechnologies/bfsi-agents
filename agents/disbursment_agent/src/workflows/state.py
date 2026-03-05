"""
Workflow State (LangGraph)

Defines the typed state that flows through the disbursement graph.
"""

from typing import TypedDict, Optional, List, Dict, Any


class DisbursementState(TypedDict, total=False):
    # ─── Input (from Decisioning Agent) ───
    application_id: str
    decision: str                           # "APPROVE" | "COUNTER_OFFER" | "DECLINE"
    risk_tier: Optional[str]
    risk_score: Optional[float]

    # Loan details (APPROVE path)
    approved_amount: Optional[float]
    approved_tenure_months: Optional[int]
    interest_rate: Optional[float]          # Annual %
    disbursement_amount: Optional[float]    # After origination fee

    # Counter offer (COUNTER_OFFER path)
    counter_offer: Optional[Dict[str, Any]]
    selected_option_id: Optional[str]

    explanation: Optional[str]

    # ─── Processing ───
    disbursement_status: str                # PENDING → VALIDATED → SCHEDULED → DISBURSED / FAILED
    validation_passed: Optional[bool]

    # ─── Schedule Generation ───
    monthly_emi: Optional[float]
    total_interest: Optional[float]
    total_repayment: Optional[float]
    first_emi_date: Optional[str]
    repayment_schedule: Optional[List[Dict[str, Any]]]

    # ─── Banking Gateway ───
    transaction_id: Optional[str]
    transfer_timestamp: Optional[str]

    # ─── Final Output ───
    disbursement_receipt: Optional[Dict[str, Any]]

    # ─── Error ───
    error: Optional[str]
