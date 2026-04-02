from pydantic import Field
from typing import List, Optional, Dict, Any, TypedDict, Annotated


def list_append_reducer(existing, new):
    existing = existing or []
    new = new or []
    return existing + new


def dict_merge_reducer(
    existing: dict[str, float] | None, new: dict[str, float] | None
) -> dict[str, float]:
    existing = existing or {}
    new = new or {}
    return {**existing, **new}

# --- Node 1: Credit Score ---
class CreditScoreMetrics(TypedDict):
    score: int
    score_band: str  # e.g., "FAIR"
    base_limit_band: float
    score_risk_flag: str  # e.g., "MODERATE"
    score_weight: float

# --- Node 2: Public Record ---
class PublicRecordMetrics(TypedDict):
    bankruptcy_present: bool
    years_since_bankruptcy: Optional[int] = None
    public_record_severity: str
    public_record_adjustment_factor: float
    hard_decline_flag: bool

# --- Node 3: Revolving Utilization ---
class UtilizationMetrics(TypedDict):
    total_credit_limit: float
    total_balance: float
    utilization_ratio: float
    utilization_risk: str
    utilization_adjustment_factor: float

# --- Node 4: Debt Exposure ---
class ExposureMetrics(TypedDict):
    total_existing_debt: float
    monthly_obligation_estimate: float
    exposure_risk: str

# --- Node 5: Inquiry Velocity ---
class InquiryMetrics(TypedDict):
    inquiries_last_12m: int
    velocity_risk: str
    inquiry_penalty_factor: float

# --- Node 6: Payment Behavior ---
class BehaviorMetrics(TypedDict):
    delinquencies: int
    chargeoff_history: bool
    behavior_score: float
    behavior_risk: str

# --- Node 7: Income (Optional) ---
class IncomeMetrics(TypedDict):
    estimated_dti: float
    income_risk: str
    affordability_flag: bool
    income_missing_flag: bool = False # Default to False if income exists

# --- Final Decision Output ---
class FinalDecision(TypedDict):
    decision: str  # "APPROVE", "COUNTER_OFFER", "DECLINE"
    approved_amount: float
    approved_tenure: int
    interest_rate: float           # Annual interest rate (e.g., 7.5)
    disbursement_amount: float     # Amount after deducting origination fee
    explanation: str
    reasoning_steps: List[str]

class LoanTermOption(TypedDict):
    option_id: str          # e.g., "OPT_LOWER_AMT" or "OPT_LONGER_TERM"
    description: str        # "Keep 36 months, reduce amount to $35k"
    proposed_amount: float
    proposed_tenure_months: int
    proposed_interest_rate: float
    disbursement_amount: float     # Amount after deducting origination fee
    monthly_payment_emi: float
    total_repayment: float

class CounterOfferMetrics(TypedDict):
    original_request_dti: float      # The DTI that caused the rejection
    max_affordable_emi: float        # The ceiling calculated by the agent
    counter_offer_logic: str         # "User DTI was 45%, limit is 40%. Reduced principal."
    generated_options: List[LoanTermOption] # List of possible restructuring options

class LoanApplicationState(TypedDict):
    # --- 1. Raw Inputs (From KYC/Intake) ---
    application_id: str
    correlation_id: str
    raw_experian_data: Dict[str, Any]  # The full JSON dump from Experian
    policy_metadata: Dict[str, Any]
    version_metadata: Dict[str, Any]
    
    pi_masked_experian_data: Dict[str, Any]  # The full JSON dump from Experian
    bank_statement_summary: Dict[str, Any]
    user_request: Dict[str, Any]       # {amount: 50000, tenure: 36}
    
    # --- 2. Processing Flags ---
    is_pii_masked: bool                # True after Node 2 (PII Masking) runs
    hard_decline_triggered: bool       # fast-fail flag
    
    # --- 3. Parallel Node Outputs (The "Fanned Out" Results) ---
    # Each parallel node populates ONE of these keys.
    credit_score_data: Optional[CreditScoreMetrics]
    public_record_data: Optional[PublicRecordMetrics]
    utilization_data: Optional[UtilizationMetrics]
    exposure_data: Optional[ExposureMetrics]
    inquiry_data: Optional[InquiryMetrics]
    behavior_data: Optional[BehaviorMetrics]
    income_data: Optional[IncomeMetrics]

    # --- 4. Aggregation Phase ---
    # The "Risk Aggregator Node" reads the sections above and populates this:
    aggregated_risk_score: Optional[float] 
    aggregated_risk_tier: Optional[str]    # "A", "B", "C", "F"
    reasoning_trace: Optional[Dict[str, Any]]

    counter_offer_data: Optional[CounterOfferMetrics]
    human_review_packet: Optional[Dict[str, Any]]
    
    # --- 5. Decision Result (for routing) ---
    decision_result: Optional[Dict[str, Any]]  # {"decision": "APPROVE"|"COUNTER_OFFER"|"DECLINE"}
    
    # --- 6. Final Output ---
    final_decision: Optional[FinalDecision]

    parallel_tasks_completed: Annotated[list[str], list_append_reducer]
    node_execution_times: Annotated[dict[str, float], dict_merge_reducer]
