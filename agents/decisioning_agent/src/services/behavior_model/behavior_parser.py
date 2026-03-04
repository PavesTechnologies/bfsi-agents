from pydantic import BaseModel, Field


class BehaviorOutput(BaseModel):
    delinquencies: int = Field(description="Number of historical missed payments (30+ days past due)")
    chargeoff_history: bool = Field(description="True if any account was ever charged off or sent to collections")
    behavior_score: float = Field(description="Score from 0 (worst) to 100 (best) based on payment history")
    behavior_risk: str = Field(description="Classification: EXCELLENT, FAIR, POOR, UNACCEPTABLE")
    confidence_score: float = Field(description="Model confidence level between 0 and 1 for the classification")
    model_reasoning: str = Field(description="Explanation for the behavioral categorization")
