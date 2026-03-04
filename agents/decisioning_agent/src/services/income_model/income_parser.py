from pydantic import BaseModel, Field


class IncomeOutput(BaseModel):
    estimated_dti: float = Field(description="Debt-to-Income ratio as a decimal (e.g., 0.35 for 35%)")
    income_risk: str = Field(description="Classification: LOW, MODERATE, HIGH, UNACCEPTABLE")
    affordability_flag: bool = Field(description="True if DTI is considered acceptable (less than or equal to 45%)")
    income_missing_flag: bool = Field(description="True if income data is missing or unverifiable")
    confidence_score: float = Field(description="Model confidence level between 0 and 1 for the classification")
    model_reasoning: str = Field(description="Explanation of the DTI calculation and risk assessment")
