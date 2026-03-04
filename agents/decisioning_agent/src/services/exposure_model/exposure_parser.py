from pydantic import BaseModel, Field


class ExposureOutput(BaseModel):
    total_existing_debt: float = Field(description="Sum of all active loan/credit balances")
    monthly_obligation_estimate: float = Field(description="Sum of minimum monthly payments across all active accounts")
    exposure_risk: str = Field(description="Classification: LOW, MODERATE, HIGH, EXTREME")
    confidence_score: float = Field(description="Model confidence level between 0 and 1 for the classification")
    model_reasoning: str = Field(description="Explanation for the exposure risk classification")
