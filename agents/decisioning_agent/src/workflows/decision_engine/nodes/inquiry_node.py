"""
Inquiry Velocity Engine
Deterministic recent credit-seeking behavior analyzer.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.calculators.inquiry_velocity import classify_inquiry_velocity
from src.policy.policy_loader import load_policy_config
from src.services.inquiry_model.inquiry_parser import InquiryOutput
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("inquiry_engine")
@audit_node(agent_name="decisioning_agent")
def inquiry_node(state: LoanApplicationState) -> LoanApplicationState:
    raw_experian = state.get("pi_masked_experian_data")
    inquiries = raw_experian.get("inquiry", [])

    result = InquiryOutput(
        **classify_inquiry_velocity(inquiries, load_policy_config())
    )
    inquiry_data = result.model_dump()
    inquiry_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"inquiry_data": inquiry_data}
