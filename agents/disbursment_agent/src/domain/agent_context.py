"""
Agent Business Context (Domain)

Represents business facts and decisions for the Disbursement Agent.
Independent of LangGraph and LLM vendors.
"""

from typing import TypedDict, Optional, List, Dict, Any
from enum import Enum


class DecisionType(str, Enum):
    """Decision types received from the Decisioning Agent."""
    APPROVE = "APPROVE"
    COUNTER_OFFER = "COUNTER_OFFER"
    DECLINE = "DECLINE"


class DisbursementStatus(str, Enum):
    """Status of the disbursement process."""
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    SCHEDULED = "SCHEDULED"
    DISBURSED = "DISBURSED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class AgentContext(TypedDict, total=False):
    # --- Input from Decisioning Agent ---
    application_id: str
    decision: str                       # "APPROVE", "COUNTER_OFFER", "DECLINE"
    risk_tier: str                      # "A", "B", "C", "F"
    risk_score: float

    # Loan details (from APPROVE)
    approved_amount: float
    approved_tenure_months: int
    interest_rate: float                # Annual interest rate (e.g., 7.5)
    disbursement_amount: float          # Amount after origination fee deduction
    explanation: str

    # Counter offer details (from COUNTER_OFFER)
    selected_option_id: Optional[str]   # User-selected counter offer option
    counter_offer: Optional[Dict[str, Any]]

    # --- Disbursement Processing ---
    disbursement_status: str
    repayment_schedule: Optional[List[Dict[str, Any]]]
    monthly_emi: Optional[float]
    total_interest: Optional[float]
    total_repayment: Optional[float]
    first_emi_date: Optional[str]

    # --- Banking Gateway ---
    transaction_id: Optional[str]
    transfer_timestamp: Optional[str]

    # --- Final Receipt ---
    disbursement_receipt: Optional[Dict[str, Any]]

    # --- Error Handling ---
    error: Optional[str]
