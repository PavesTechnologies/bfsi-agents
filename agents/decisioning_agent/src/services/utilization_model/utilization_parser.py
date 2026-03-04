from pydantic import BaseModel, Field


class UtilizationOutput(BaseModel):
    total_credit_limit: float = Field(description="Sum of all revolving credit limits")
    total_balance: float = Field(description="Sum of all revolving balances")
    utilization_ratio: float = Field(description="Calculated as total_balance / total_credit_limit")
    utilization_risk: str = Field(description="Classification: EXCELLENT, GOOD, HIGH, CRITICAL")
    utilization_adjustment_factor: float = Field(description="Multiplier based on utilization risk tier")
    confidence_score: float = Field(description="Model confidence level between 0 and 1 for the classification")
    model_reasoning: str = Field(description="Explanation for the utilization classification")
