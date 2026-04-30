from typing import Literal

from pydantic import BaseModel, Field


class InquiryOutput(BaseModel):
    inquiries_last_12m: int = Field(description="Number of hard inquiries in the last 12 months")
    velocity_risk: str = Field(description="Classification: LOW, MODERATE, HIGH")
    inquiry_penalty_factor: float = Field(description="Penalty factor to apply based on inquiry velocity")
    confidence_score: float = Field(description="Model confidence level between 0 and 1 for the classification")
    model_reasoning: str = Field(description="Explanation for the given classification")
    llm_response_type: Literal["RAG", "FALLBACK"] = Field(
        description="RAG if POLICY GUIDANCE excerpts drove the values, FALLBACK if FALLBACK DEFAULTS were used"
    )
