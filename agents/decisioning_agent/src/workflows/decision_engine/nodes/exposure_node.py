"""
Debt Exposure Engine
Deterministic outstanding liability evaluator.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.calculators.exposure import classify_exposure
from src.services.exposure_model.exposure_parser import ExposureOutput
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("exposure_engine")
@audit_node(agent_name="decisioning_agent")
def exposure_node(state: LoanApplicationState) -> LoanApplicationState:
    raw_experian = state.get("pi_masked_experian_data")
    tradelines = raw_experian.get("tradeline", [])
    open_trades = [
        trade for trade in tradelines if trade.get("openOrClosed") == "O"
    ]

    result = ExposureOutput(**classify_exposure(open_trades))
    exposure_data = result.model_dump()
    exposure_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"exposure_data": exposure_data}
