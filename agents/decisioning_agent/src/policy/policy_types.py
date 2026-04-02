"""Typed policy contracts for deterministic underwriting."""

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class BankMetadata(BaseModel):
    id: str
    policy_version: str
    last_updated: Optional[str | date] = None


class ScoreBandPolicy(BaseModel):
    min: int
    max: int
    risk: str
    base_limit: float


class CreditScorePolicy(BaseModel):
    bands: Dict[str, ScoreBandPolicy]


class BankruptcyPolicy(BaseModel):
    enabled: bool = True
    hard_decline_if_within_years: int = 2
    severity_by_age: Dict[str, str] = Field(default_factory=dict)
    adjustment_factor_by_age: Dict[str, float] = Field(default_factory=dict)


class PublicRecordsPolicy(BaseModel):
    bankruptcy: BankruptcyPolicy


class UtilizationBandPolicy(BaseModel):
    max: float
    risk: str
    factor: float


class UtilizationPolicy(BaseModel):
    bands: Dict[str, UtilizationBandPolicy]


class InquiryBandPolicy(BaseModel):
    max_last_12m: int
    risk: str
    factor: float


class InquiryVelocityPolicy(BaseModel):
    bands: Dict[str, InquiryBandPolicy]


class DelinquencyRulesPolicy(BaseModel):
    clean_threshold: int
    moderate_threshold: int
    severe_threshold: int


class ChargeoffPenaltyPolicy(BaseModel):
    present_factor: float
    absent_factor: float


class PaymentBehaviorPolicy(BaseModel):
    delinquency_rules: DelinquencyRulesPolicy
    chargeoff_penalty: ChargeoffPenaltyPolicy


class DtiBandPolicy(BaseModel):
    max: float
    risk: str


class AffordabilityPolicy(BaseModel):
    dti_bands: Dict[str, DtiBandPolicy]


class RiskWeightsPolicy(BaseModel):
    credit_score: float
    utilization: float
    payment_behavior: float
    public_records: float
    inquiries: float
    affordability: float

    @model_validator(mode="after")
    def validate_total(self):
        total = (
            self.credit_score
            + self.utilization
            + self.payment_behavior
            + self.public_records
            + self.inquiries
            + self.affordability
        )
        if round(total, 6) != 1.0:
            raise ValueError("risk_weights must sum to 1.0")
        return self


class FeatureFlagsPolicy(BaseModel):
    enable_public_records: bool = True
    enable_income_check: bool = True
    enable_inquiry_penalty: bool = True


class PolicyMetadata(BaseModel):
    risk_engine_version: Optional[str] = None
    environment: Optional[str] = None
    document_version: str = "doc-v1"
    retrieval_index_version: str = "retrieval-v1"


class ReviewGatePolicy(BaseModel):
    borderline_tiers: List[str] = Field(default_factory=lambda: ["D"])
    refer_when_income_missing: bool = True
    refer_when_thin_file: bool = True


class ProductEligibilityPolicy(BaseModel):
    product_code: str = "UNSECURED_PERSONAL_LOAN"
    min_tradelines: int = 3
    min_credit_age_months: int = 24
    minimum_credit_score: int = 600


class PolicyCitationMetadata(BaseModel):
    policy_id: str = "UPL_POLICY"
    product: str = "UNSECURED_PERSONAL_LOAN"
    default_document_name: str = "unsecured_personal_loans_policy_v1.md"


class RiskTierThresholdPolicy(BaseModel):
    threshold: float
    tier: str


class UnderwritingPolicy(BaseModel):
    bank: BankMetadata
    credit_score: CreditScorePolicy
    public_records: PublicRecordsPolicy
    utilization: UtilizationPolicy
    inquiry_velocity: InquiryVelocityPolicy
    payment_behavior: PaymentBehaviorPolicy
    affordability: AffordabilityPolicy
    risk_weights: RiskWeightsPolicy
    features: FeatureFlagsPolicy
    metadata: PolicyMetadata
    review_gates: ReviewGatePolicy = Field(default_factory=ReviewGatePolicy)
    product_eligibility: ProductEligibilityPolicy = Field(default_factory=ProductEligibilityPolicy)
    policy_citation: PolicyCitationMetadata = Field(default_factory=PolicyCitationMetadata)
    risk_tiers: List[RiskTierThresholdPolicy] = Field(
        default_factory=lambda: [
            RiskTierThresholdPolicy(threshold=80, tier="A"),
            RiskTierThresholdPolicy(threshold=65, tier="B"),
            RiskTierThresholdPolicy(threshold=50, tier="C"),
            RiskTierThresholdPolicy(threshold=35, tier="D"),
            RiskTierThresholdPolicy(threshold=0, tier="F"),
        ]
    )
