"""
Counter Offer Structuring Engine
Affordability-Based Restructuring Logic
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node

from src.services.llm_executor import execute_llm
from src.services.counter_offer_model.counter_offer_parser import CounterOfferOutput
from src.services.counter_offer_model.counter_offer_prompt import COUNTER_OFFER_PROMPT


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
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    counter_offer_data = result.model_dump()
    counter_offer_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"counter_offer_data": counter_offer_data}