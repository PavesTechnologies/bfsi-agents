"""Build a structured underwriting human-review packet."""

from src.core.telemetry import track_node
from src.domain.review.review_packet_builder import build_reviewer_packet
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("underwriting_human_review_packet")
@audit_node(agent_name="decisioning_agent")
def human_review_packet_node(state: LoanApplicationState) -> LoanApplicationState:
    packet = build_reviewer_packet(
        application_id=state.get("application_id"),
        aggregated_risk_tier=state.get("aggregated_risk_tier"),
        aggregated_risk_score=state.get("aggregated_risk_score"),
        credit_score_data=state.get("credit_score_data", {}),
        public_record_data=state.get("public_record_data", {}),
        utilization_data=state.get("utilization_data", {}),
        exposure_data=state.get("exposure_data", {}),
        inquiry_data=state.get("inquiry_data", {}),
        behavior_data=state.get("behavior_data", {}),
        income_data=state.get("income_data", {}),
        user_request=state.get("user_request", {}),
        final_decision=state.get("final_decision", {}),
    )
    return {"human_review_packet": packet}
