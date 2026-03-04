from pydantic import BaseModel, Field
from typing import Optional


class PublicRecordOutput(BaseModel):
    bankruptcy_present: bool = Field(description="True if any bankruptcy is found in the public records")
    years_since_bankruptcy: Optional[int] = Field(None, description="Years since the most recent bankruptcy, if applicable")
    public_record_severity: str = Field(description="Classification: NONE, LOW, MODERATE, SEVERE")
    public_record_adjustment_factor: float = Field(description="Score penalty multiplier (e.g., 1.0 for NONE, 0.5 for SEVERE)")
    hard_decline_flag: bool = Field(description="True if severity is SEVERE or bankruptcy is less than 2 years old")
    confidence_score: float = Field(description="Model confidence level between 0 and 1 for the classification")
    model_reasoning: str = Field(description="Explanation for the public record classification")
