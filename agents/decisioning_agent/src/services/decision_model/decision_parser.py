from pydantic import BaseModel, Field
from typing import List


class DecisionOutput(BaseModel):
    decision: str = Field(description="One of: APPROVE, COUNTER_OFFER, DECLINE")
    approved_amount: float = Field(description="Loan amount approved (0 if declined)")
    approved_tenure: int = Field(description="Approved repayment tenure in months (0 if declined)")
    interest_rate: float = Field(description="Annual interest rate percentage (e.g., 7.5 for 7.5%)")
    disbursement_amount: float = Field(description="Net amount disbursed after deducting origination fee (2% of approved amount)")
    explanation: str = Field(description="Clear explanation of the decision")
    reasoning_steps: List[str] = Field(description="Step-by-step reasoning that led to the decision")
    confidence_score: float = Field(description="Model confidence level between 0 and 1")
