"""
Underwriting Decision Engine (LLM Layer)
Multi-Factor Risk Interpretation & Policy Routing
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState

from src.services.llm_executor import execute_llm
from src.services.decision_model.decision_parser import DecisionOutput
from src.services.decision_model.decision_prompt import DECISION_PROMPT


@track_node("underwriting_decision_engine")
def decision_llm_node(state: LoanApplicationState) -> LoanApplicationState:

    decision_output_parser = PydanticOutputParser(
        pydantic_object=DecisionOutput
    )

    # ==================================================
    # 1️⃣ Extract Aggregated Risk Profile
    # ==================================================
    user_request = state.get("user_request", {})
    credit_score_data = state.get("credit_score_data", {})
    public_record_data = state.get("public_record_data", {})
    utilization_data = state.get("utilization_data", {})
    exposure_data = state.get("exposure_data", {})
    behavior_data = state.get("behavior_data", {})
    inquiry_data = state.get("inquiry_data", {})
    income_data = state.get("income_data", {})

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "aggregated_risk_score": str(state.get("aggregated_risk_score", 0)),
        "aggregated_risk_tier": str(state.get("aggregated_risk_tier", "F")),
        "credit_score_data": json.dumps(credit_score_data),
        "public_record_data": json.dumps(public_record_data),
        "utilization_data": json.dumps(utilization_data),
        "exposure_data": json.dumps(exposure_data),
        "behavior_data": json.dumps(behavior_data),
        "inquiry_data": json.dumps(inquiry_data),
        "income_data": json.dumps(income_data),
        "requested_amount": str(user_request.get("amount", 0)),
        "requested_tenure": str(user_request.get("tenure", 0)),
        "format_instructions": decision_output_parser.get_format_instructions(),
    }

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=DECISION_PROMPT,
        inputs=inputs,
        parser=decision_output_parser,
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    final_decision = result.model_dump()
    final_decision["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # decision_result is used by the conditional router in decision_flow.py
    decision_result = {"decision": final_decision["decision"]}

    return {
        "final_decision": final_decision,
        "decision_result": decision_result,
    }