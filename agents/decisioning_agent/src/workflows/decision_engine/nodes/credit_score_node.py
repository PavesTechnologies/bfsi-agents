"""
Credit Score Evaluation Engine
Policy-driven deterministic bureau score interpreter.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.calculators.credit_banding import classify_credit_score
from src.policy.policy_registry import get_active_policy
from src.services.credit_score_model.credit_score_parser import CreditScoreOutput
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("credit_score_engine")
@audit_node(agent_name="decisioning_agent")
def credit_score_node(state: LoanApplicationState) -> LoanApplicationState:
    raw_experian = state.get("pi_masked_experian_data")
    risk_model = raw_experian.get("riskModel", [])

    score = 0
    if risk_model:
        score = int(risk_model[0].get("score", 0))

    tradelines = raw_experian.get("tradeline", [])
    credit_age_months = 0
    if tradelines:
        credit_age_months = max(
            int(trade.get("monthsSinceOpened", 0) or 0)
            for trade in tradelines
        )

    policy = get_active_policy()
    result = CreditScoreOutput(
        **classify_credit_score(score, policy.model_dump())
    )
    credit_score_data = result.model_dump()
    credit_score_data["tradeline_count"] = len(tradelines)
    credit_score_data["credit_age_months"] = credit_age_months
    credit_score_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"credit_score_data": credit_score_data}
