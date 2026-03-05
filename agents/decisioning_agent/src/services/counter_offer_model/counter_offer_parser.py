from pydantic import BaseModel, Field
from typing import List


class CounterOfferOption(BaseModel):
    option_id: str = Field(description="Unique option identifier, e.g., OPT_LOWER_AMT, OPT_LONGER_TERM")
    description: str = Field(description="Human-readable description of the option")
    proposed_amount: float = Field(description="Proposed loan amount for this option")
    proposed_tenure_months: int = Field(description="Proposed repayment tenure in months")
    proposed_interest_rate: float = Field(description="Annual interest rate for this option (percentage)")
    disbursement_amount: float = Field(description="Net disbursement after deducting origination fee (2%)")
    monthly_payment_emi: float = Field(description="Estimated monthly EMI payment")
    total_repayment: float = Field(description="Total amount repaid over the full tenure")


class CounterOfferOutput(BaseModel):
    original_request_dti: float = Field(description="The DTI ratio that contributed to the rejection")
    max_affordable_emi: float = Field(description="Maximum monthly EMI the applicant can afford")
    counter_offer_logic: str = Field(description="Explanation of why the original request was rejected and how counter offers were structured")
    generated_options: List[CounterOfferOption] = Field(description="List of 2-3 restructured loan options")
    confidence_score: float = Field(description="Model confidence level between 0 and 1")
