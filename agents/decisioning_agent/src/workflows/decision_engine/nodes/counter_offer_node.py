"""
Counter Offer Structuring Engine
Affordability-based deterministic restructuring logic.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.calculators.counter_offer import generate_counter_offer
from src.services.counter_offer_model.counter_offer_parser import CounterOfferOutput
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("counter_offer_engine")
@audit_node(agent_name="decisioning_agent")
def counter_offer_node(state: LoanApplicationState) -> LoanApplicationState:
    user_request = state.get("user_request", {})
    credit_score_data = state.get("credit_score_data", {})
    income_data = state.get("income_data", {})
    exposure_data = state.get("exposure_data", {})

    result = CounterOfferOutput(
        **generate_counter_offer(
            risk_tier=str(state.get("aggregated_risk_tier", "D")),
            base_limit=float(credit_score_data.get("base_limit_band", 0) or 0),
            requested_amount=float(user_request.get("amount", 0) or 0),
            requested_tenure=int(user_request.get("tenure", 0) or 0),
            monthly_income=float(
                state.get("bank_statement_summary", {}).get("monthly_income", 0) or 0
            ),
            monthly_obligations=float(
                exposure_data.get("monthly_obligation_estimate", 0) or 0
            ),
            original_request_dti=float(income_data.get("estimated_dti", 0) or 0),
        )
    )

    counter_offer_data = result.model_dump()
    counter_offer_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"counter_offer_data": counter_offer_data}
