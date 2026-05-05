from pydantic import BaseModel, Field
from typing import List


class DecisionOutput(BaseModel):
    decision: str = Field(description="One of: APPROVE, COUNTER_OFFER, DECLINE")
    approved_amount: float = Field(description="Loan amount approved (0 if declined or counter-offer)")
    approved_tenure: int = Field(description="Approved repayment tenure in months (0 if declined or counter-offer)")
    interest_rate: float = Field(description="Annual interest rate percentage (e.g., 7.5 for 7.5%)")
    disbursement_amount: float = Field(description="Net amount disbursed after deducting origination fee (2% of approved amount)")
    max_approved_amount: float = Field(
        description=(
            "Maximum amount the borrower qualifies for after applying all adjustment factors. "
            "Always set this. Used in the COUNTER_OFFER branch so the borrower sees their cap."
        )
    )
    explanation: str = Field(description="Clear explanation of the decision")
    reasoning_steps: List[str] = Field(description="Step-by-step reasoning that led to the decision")
    confidence_score: float = Field(description="Model confidence level between 0 and 1")
