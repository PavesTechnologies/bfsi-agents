"""
Underwriting Decision Engine
Deterministic policy routing for underwriting outcomes.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.attribution.rule_attribution import build_rule_attribution
from src.domain.decisioning.decision_engine import make_underwriting_decision
from src.services.decision_model.explanation_service import build_cited_explanation
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("underwriting_decision_engine")
@audit_node(agent_name="decisioning_agent")
def decision_llm_node(state: LoanApplicationState) -> LoanApplicationState:
    result = make_underwriting_decision(
        aggregated_risk_tier=str(state.get("aggregated_risk_tier", "F")),
        credit_score_data=state.get("credit_score_data", {}),
        public_record_data=state.get("public_record_data", {}),
        utilization_data=state.get("utilization_data", {}),
        inquiry_data=state.get("inquiry_data", {}),
        income_data=state.get("income_data", {}),
        behavior_data=state.get("behavior_data", {}),
        exposure_data=state.get("exposure_data", {}),
        user_request=state.get("user_request", {}),
    )

    final_decision = result.model_dump()
    explanation_bundle = build_cited_explanation(deterministic_outcome=final_decision)
    final_decision["explanation"] = explanation_bundle["explanation_text"]
    final_decision["policy_citations"] = [
        {
            "section_id": item.get("section_id"),
            "section_title": item.get("section_title"),
            "source_path": item.get("source_path"),
        }
        for item in explanation_bundle.get("policy_evidence", [])
    ]
    final_decision["retrieval_evidence"] = explanation_bundle.get("policy_evidence", [])
    final_decision["explanation_generation_mode"] = explanation_bundle.get("generation_mode")
    final_decision["critic_failures"] = explanation_bundle.get("critic_failures", [])
    final_decision["feature_attribution_summary"] = {
        "rule_attribution": build_rule_attribution(
            income_data=state.get("income_data", {}),
            public_record_data=state.get("public_record_data", {}),
            utilization_data=state.get("utilization_data", {}),
            exposure_data=state.get("exposure_data", {}),
            inquiry_data=state.get("inquiry_data", {}),
            behavior_data=state.get("behavior_data", {}),
        ),
        "score_contribution": (state.get("reasoning_trace") or {}).get("score_contribution", []),
    }
    final_decision["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    decision_result = {"decision": final_decision["decision"]}

    return {
        "final_decision": final_decision,
        "decision_result": decision_result,
    }
