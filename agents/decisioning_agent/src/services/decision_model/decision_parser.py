from pydantic import BaseModel, Field
from typing import List, Optional


class DecisionOutput(BaseModel):
    decision: str = Field(description="One of: APPROVE, COUNTER_OFFER, DECLINE, REFER_TO_HUMAN")
    approved_amount: float = Field(description="Loan amount approved (0 if declined)")
    approved_tenure: int = Field(description="Approved repayment tenure in months (0 if declined)")
    interest_rate: float = Field(description="Annual interest rate percentage (e.g., 7.5 for 7.5%)")
    disbursement_amount: float = Field(description="Net amount disbursed after deducting origination fee (2% of approved amount)")
    explanation: str = Field(description="Clear explanation of the decision")
    reasoning_steps: List[str] = Field(description="Step-by-step reasoning that led to the decision")
    confidence_score: float = Field(description="Model confidence level between 0 and 1")
    primary_reason_key: Optional[str] = Field(default=None, description="Primary mapped regulatory decline reason key")
    secondary_reason_key: Optional[str] = Field(default=None, description="Secondary mapped regulatory decline reason key")
    adverse_action_reasons: Optional[List[dict]] = Field(default=None, description="Mapped regulatory adverse action reasons")
    adverse_action_notice: Optional[str] = Field(default=None, description="Disclosure-safe notice text built from mapped reasons")
    reasoning_summary: Optional[str] = Field(default=None, description="Short deterministic summary of the decline rationale")
    key_factors: Optional[List[str]] = Field(default=None, description="Top internal factors supporting the decision")
    candidate_reason_codes: Optional[List[dict]] = Field(default=None, description="All triggered candidate reasons prior to final selection")
    selected_reason_codes: Optional[List[dict]] = Field(default=None, description="Selected reason-code artifacts including internal/reviewer text")
    policy_citations: Optional[List[dict]] = Field(default=None, description="Policy evidence used for explanation generation")
    retrieval_evidence: Optional[List[dict]] = Field(default=None, description="Retrieved policy chunks")
    feature_attribution_summary: Optional[dict] = Field(default=None, description="Structured attribution summary for the final outcome")
    explanation_generation_mode: Optional[str] = Field(default=None, description="LLM or deterministic explanation mode")
    critic_failures: Optional[List[str]] = Field(default=None, description="Explanation critic failures when fallback was required")
