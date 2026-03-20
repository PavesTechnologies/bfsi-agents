"""
Underwriting Decision Engine (LLM Layer)
Multi-Factor Risk Interpretation & Policy Routing
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node

from src.services.llm_executor import execute_llm
from src.services.decision_model.decision_parser import DecisionOutput
from src.services.decision_model.decision_prompt import DECISION_PROMPT


def _build_fallback_decision(state: LoanApplicationState) -> DecisionOutput:
    user_request = state.get("user_request", {})
    requested_amount = float(user_request.get("amount", 0) or 0)
    requested_tenure = int(user_request.get("tenure", 0) or 0)
    risk_score = float(state.get("aggregated_risk_score", 0) or 0)

    if risk_score >= 75:
        return DecisionOutput(
            decision="APPROVE",
            approved_amount=requested_amount,
            approved_tenure=requested_tenure,
            interest_rate=12.0,
            disbursement_amount=round(requested_amount * 0.98, 2),
            explanation="Fallback approval generated from deterministic risk thresholds.",
            reasoning_steps=[
                "LLM decision output was unavailable.",
                "Deterministic underwriting fallback approved the request.",
            ],
            confidence_score=0.0,
        )

    if risk_score >= 55:
        reduced_amount = round(requested_amount * 0.8, 2)
        extended_tenure = max(requested_tenure, 24)
        return DecisionOutput(
            decision="COUNTER_OFFER",
            approved_amount=reduced_amount,
            approved_tenure=extended_tenure,
            interest_rate=14.5,
            disbursement_amount=round(reduced_amount * 0.98, 2),
            explanation="Fallback counter offer generated from deterministic risk thresholds.",
            reasoning_steps=[
                "LLM decision output was unavailable.",
                "Deterministic underwriting fallback reduced the amount and extended tenure.",
            ],
            confidence_score=0.0,
        )

    return DecisionOutput(
        decision="DECLINE",
        approved_amount=0.0,
        approved_tenure=0,
        interest_rate=0.0,
        disbursement_amount=0.0,
        explanation="Fallback decline generated because the aggregated risk score is below policy threshold.",
        reasoning_steps=[
            "LLM decision output was unavailable.",
            "Deterministic underwriting fallback declined the request.",
        ],
        confidence_score=0.0,
    )


@track_node("underwriting_decision_engine")
@audit_node(agent_name="decisioning_agent")
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
        fallback_result=lambda: _build_fallback_decision(state),
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
