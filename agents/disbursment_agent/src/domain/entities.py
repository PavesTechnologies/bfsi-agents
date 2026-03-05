"""
Domain Entities for the Disbursement Agent.

Pydantic models representing core business objects.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class DisbursementRequest(BaseModel):
    """Input payload received from the Decisioning Agent."""
    application_id: str = Field(description="Unique loan application identifier")
    decision: str = Field(description="Decision from decisioning agent: APPROVE, COUNTER_OFFER, DECLINE")
    risk_tier: Optional[str] = Field(default=None, description="Aggregated risk tier: A, B, C, F")
    risk_score: Optional[float] = Field(default=None, description="Aggregated risk score")

    # Loan details (populated for APPROVE)
    loan_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Loan details: approved_amount, approved_tenure_months, interest_rate, disbursement_amount"
    )

    # Counter offer (populated for COUNTER_OFFER)
    counter_offer: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Counter offer data from decisioning agent"
    )
    selected_option_id: Optional[str] = Field(
        default=None,
        description="User-selected counter offer option ID (e.g., OPT_LOWER_AMT)"
    )

    # Decline info
    decline_reason: Optional[str] = Field(default=None, description="Reason for decline")


class EMIInstallment(BaseModel):
    """A single EMI installment in the repayment schedule."""
    installment_number: int
    due_date: str
    opening_balance: float
    emi_amount: float
    principal_component: float
    interest_component: float
    closing_balance: float


class RepaymentSchedule(BaseModel):
    """Full amortization / repayment schedule."""
    principal: float = Field(description="Original loan principal")
    annual_interest_rate: float = Field(description="Annual interest rate (%)")
    tenure_months: int = Field(description="Loan tenure in months")
    monthly_emi: float = Field(description="Fixed monthly EMI amount")
    total_interest: float = Field(description="Total interest payable over the loan")
    total_repayment: float = Field(description="Total amount repayable (principal + interest)")
    first_emi_date: str = Field(description="Date of the first EMI")
    installments: List[EMIInstallment] = Field(description="Month-by-month amortization schedule")


class DisbursementReceipt(BaseModel):
    """Final output receipt after disbursement is complete."""
    application_id: str
    disbursement_status: str            # "DISBURSED", "FAILED", "REJECTED"
    decision_type: str                  # "APPROVE" or "COUNTER_OFFER"

    # Amounts
    approved_amount: float
    disbursement_amount: float          # Net amount transferred
    origination_fee_deducted: float     # Fee that was deducted

    # Loan Terms
    interest_rate: float
    tenure_months: int
    monthly_emi: float
    total_interest: float
    total_repayment: float
    first_emi_date: str

    # Transfer Details
    transaction_id: Optional[str] = None
    transfer_timestamp: Optional[str] = None

    # Schedule summary (first 3 + last installment)
    schedule_preview: Optional[List[EMIInstallment]] = None

    # Explanation
    explanation: Optional[str] = None
