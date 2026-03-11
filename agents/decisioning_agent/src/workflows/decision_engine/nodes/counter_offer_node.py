"""
Counter Offer Structuring Engine
Affordability-Based Restructuring Logic
"""

from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node

from src.services.llm_executor import execute_llm
from src.services.counter_offer_model.counter_offer_parser import CounterOfferOutput
from src.services.counter_offer_model.counter_offer_prompt import COUNTER_OFFER_PROMPT


def _build_fallback_counter_offer(state: LoanApplicationState) -> CounterOfferOutput:
    user_request = state.get("user_request", {})
    requested_amount = float(user_request.get("amount", 0) or 0)
    requested_tenure = int(user_request.get("tenure", 0) or 0)
    monthly_income = float(
        state.get("bank_statement_summary", {}).get("monthly_income", 0) or 0
    )

    option_one_amount = round(requested_amount * 0.85, 2)
    option_two_amount = round(requested_amount * 0.7, 2)
    option_one_tenure = max(requested_tenure, 24)
    option_two_tenure = max(requested_tenure + 12, 36)
    max_affordable_emi = round(monthly_income * 0.35, 2)

    return CounterOfferOutput(
        original_request_dti=float(state.get("income_data", {}).get("estimated_dti", 0) or 0),
        max_affordable_emi=max_affordable_emi,
        counter_offer_logic="Fallback counter offer generated from affordability thresholds.",
        generated_options=[
            {
                "option_id": "OPT_REDUCED_AMOUNT",
                "description": "Reduce principal while keeping a standard term.",
                "proposed_amount": option_one_amount,
                "proposed_tenure_months": option_one_tenure,
                "proposed_interest_rate": 14.5,
                "disbursement_amount": round(option_one_amount * 0.98, 2),
                "monthly_payment_emi": round(max_affordable_emi * 0.95, 2),
                "total_repayment": round(max_affordable_emi * 0.95 * option_one_tenure, 2),
            },
            {
                "option_id": "OPT_EXTENDED_TERM",
                "description": "Extend term to lower monthly obligation.",
                "proposed_amount": option_two_amount,
                "proposed_tenure_months": option_two_tenure,
                "proposed_interest_rate": 13.75,
                "disbursement_amount": round(option_two_amount * 0.98, 2),
                "monthly_payment_emi": round(max_affordable_emi * 0.8, 2),
                "total_repayment": round(max_affordable_emi * 0.8 * option_two_tenure, 2),
            },
        ],
        confidence_score=0.0,
    )


@track_node("counter_offer_engine")
@audit_node(agent_name="decisioning_agent")
def counter_offer_node(state: LoanApplicationState) -> LoanApplicationState:

    counter_offer_output_parser = PydanticOutputParser(
        pydantic_object=CounterOfferOutput
    )

    # ==================================================
    # 1️⃣ Extract Profile Data
    # ==================================================
    user_request = state.get("user_request", {})
    credit_score_data = state.get("credit_score_data", {})
    income_data = state.get("income_data", {})
    exposure_data = state.get("exposure_data", {})
    utilization_data = state.get("utilization_data", {})
    behavior_data = state.get("behavior_data", {})

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "risk_tier": str(state.get("aggregated_risk_tier", "D")),
        "score_band": str(credit_score_data.get("score_band", "FAIR")),
        "base_limit": str(credit_score_data.get("base_limit_band", 20000)),
        "estimated_dti": str(income_data.get("estimated_dti", 0)),
        "monthly_obligations": str(exposure_data.get("monthly_obligation_estimate", 0)),
        "affordability_flag": str(income_data.get("affordability_flag", False)),
        "utilization_risk": str(utilization_data.get("utilization_risk", "HIGH")),
        "behavior_risk": str(behavior_data.get("behavior_risk", "FAIR")),
        "requested_amount": str(user_request.get("amount", 0)),
        "requested_tenure": str(user_request.get("tenure", 0)),
        "format_instructions": counter_offer_output_parser.get_format_instructions(),
    }

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=COUNTER_OFFER_PROMPT,
        inputs=inputs,
        parser=counter_offer_output_parser,
        fallback_result=lambda: _build_fallback_counter_offer(state),
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    counter_offer_data = result.model_dump()
    counter_offer_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"counter_offer_data": counter_offer_data}
