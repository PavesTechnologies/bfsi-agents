"""
Behavioral Risk Engine
Deterministic payment pattern and charge-off detector.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.calculators.behavior import classify_behavior
from src.policy.policy_loader import load_policy_config
from src.services.behavior_model.behavior_parser import BehaviorOutput
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("behavior_engine")
@audit_node(agent_name="decisioning_agent")
def behavior_node(state: LoanApplicationState) -> LoanApplicationState:
    raw_experian = state.get("pi_masked_experian_data")
    tradelines = raw_experian.get("tradeline", [])

    result = BehaviorOutput(
        **classify_behavior(tradelines, load_policy_config())
    )
    behavior_data = result.model_dump()
    behavior_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"behavior_data": behavior_data}
