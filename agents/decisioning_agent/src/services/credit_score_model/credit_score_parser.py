from pydantic import BaseModel, Field

class CreditScoreOutput(BaseModel):
    score: int = Field(description="Credit score extracted from bureau report")
    score_band: str = Field(description="Score classification: PRIME, NEAR_PRIME, FAIR, SUBPRIME")
    base_limit_band: float = Field(description="Base lending limit allowed for this score band")
    score_risk_flag: str = Field(description="Risk level classification")
    score_weight: float = Field(description="Weight of credit score in risk aggregation")
    confidence_score: float = Field(
        description="Model confidence level between 0 and 1 for the classification"
    )

    model_reasoning: str = Field(
        description="Short explanation describing why the score belongs to this band"
    )