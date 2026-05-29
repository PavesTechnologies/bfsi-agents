from pydantic import BaseModel, Field
from typing import List


# ─── LLM-facing schema (text fields only) ─────────────────────────────────────
#
# The LLM is given pre-computed numbers and asked only to write justification
# text. This schema deliberately contains NO numeric loan fields — the LLM
# cannot hallucinate or drift any financial figure.

class CounterOfferJustificationOutput(BaseModel):
    counter_offer_logic: str = Field(
        description=(
            "2-3 sentences in plain language. Why was the original loan request not approved? "
            "Reference the applicant's qualifying cap, DTI, and income. No financial jargon."
        )
    )
    co1_justification: str = Field(
        description=(
            "2 sentences. Why is the reduced amount with the original tenure "
            "appropriate for this applicant's financial profile?"
        )
    )
    co2_justification: str = Field(
        description=(
            "2 sentences. Why does extending the tenure make the full requested amount viable? "
            "If CO2 was not feasible, explain in plain language why the income cannot support "
            "the full amount even at the maximum allowed tenure."
        )
    )
    co3_justification: str = Field(
        description=(
            "2 sentences. Why does this balanced option — partial amount reduction combined "
            "with a moderate tenure extension — serve the applicant better than the two extremes?"
        )
    )
    recommendation_rationale: str = Field(
        description=(
            "1 sentence. Why is the recommended option the best fit for this applicant's "
            "current financial profile?"
        )
    )
    confidence_score: float = Field(
        description="Model confidence in the justifications, between 0.0 and 1.0."
    )


# ─── Final output schema ───────────────────────────────────────────────────────
#
# All numeric fields are Python-computed and written by counter_offer_node
# AFTER the LLM call. Text fields (justification, counter_offer_logic,
# recommendation_rationale) come from CounterOfferJustificationOutput above.

class CounterOfferOption(BaseModel):
    option_id: str = Field(description="CO1 | CO2 | CO3")
    label: str = Field(description="Reduced Amount | Extended Tenure | Balanced Option")
    proposed_amount: float = Field(description="Loan principal — Python-computed")
    proposed_tenure_months: int = Field(description="Repayment tenure in months — Python-computed")
    proposed_interest_rate: float = Field(description="Annual interest rate % — Python-computed")
    monthly_payment_emi: float = Field(description="Monthly EMI — Python-computed")
    disbursement_amount: float = Field(description="Net disbursement after origination fee — Python-computed")
    total_repayment: float = Field(description="Total amount repaid over full tenure — Python-computed")
    affordability_headroom_pct: float = Field(
        description=(
            "Percentage headroom below affordability ceiling: "
            "((max_affordable_emi - emi) / max_affordable_emi) × 100. "
            "Python-computed."
        )
    )
    is_recommended: bool = Field(description="True on the system-recommended offer — Python-computed")
    feasible: bool = Field(
        description="False only for CO2 when income cannot support the full amount at any tenure"
    )
    justification: str = Field(description="LLM-generated: 2-sentence explanation for this offer")


class CounterOfferOutput(BaseModel):
    original_request_dti: float = Field(description="DTI ratio that contributed to the rejection")
    max_affordable_emi: float = Field(description="Maximum monthly EMI the applicant can afford")
    monthly_income: float = Field(description="Verified monthly income used in affordability calculation")
    existing_monthly_obligations: float = Field(description="Existing monthly EMI obligations")
    qualifying_cap: float = Field(description="Maximum principal the applicant qualifies for")
    counter_offer_logic: str = Field(description="LLM: plain-language explanation of why original was rejected")
    generated_options: List[CounterOfferOption] = Field(description="2-3 restructured loan options")
    recommended_option_id: str = Field(description="CO1 | CO2 | CO3 — Python rule-based recommendation")
    recommendation_rationale: str = Field(description="LLM: one sentence explaining the recommendation")
    confidence_score: float = Field(description="LLM confidence between 0.0 and 1.0")
    expires_at: str = Field(description="ISO timestamp: offer is valid for 10 days from generation")
