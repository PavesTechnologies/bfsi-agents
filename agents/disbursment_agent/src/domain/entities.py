"""
Domain entities for the disbursement agent.

DisbursementRequest accepts pre-resolved loan terms — the caller
(decisioning_agent /confirm or /select-offer) is responsible for
resolving the correct terms before invoking disbursement.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class DisbursementRequest(BaseModel):
    """Input payload — flat, decision-type-agnostic loan terms."""
    application_id: str = Field(description="Unique loan application identifier")
    approved_amount: float = Field(description="Approved loan principal")
    approved_tenure_months: int = Field(description="Repayment tenure in months")
    interest_rate: float = Field(description="Annual interest rate (%)")
    disbursement_amount: float = Field(description="Net amount to transfer (after origination fee)")
    explanation: Optional[str] = Field(default=None, description="Decision explanation from upstream")


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
    transfer_status: Optional[str] = None
    transfer_timestamp: Optional[str] = None
    reconciliation_required: Optional[bool] = None

    # Schedule summary (first 3 + last installment)
    schedule_preview: Optional[List[EMIInstallment]] = None

    # Explanation
    explanation: Optional[str] = None