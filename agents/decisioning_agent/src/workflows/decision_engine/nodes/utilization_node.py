"""
Revolving Utilization Engine
Deterministic exposure stress analyzer.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.calculators.utilization import classify_utilization
from src.policy.policy_loader import load_policy_config
from src.services.utilization_model.utilization_parser import UtilizationOutput
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("utilization_engine")
@audit_node(agent_name="decisioning_agent")
def utilization_node(state: LoanApplicationState) -> LoanApplicationState:
    raw_experian = state.get("pi_masked_experian_data")
    tradelines = raw_experian.get("tradeline", [])
    revolving_trades = [
        trade for trade in tradelines if trade.get("revolvingOrInstallment") == "R"
    ]

    result = UtilizationOutput(
        **classify_utilization(revolving_trades, load_policy_config())
    )
    utilization_data = result.model_dump()
    utilization_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"utilization_data": utilization_data}
