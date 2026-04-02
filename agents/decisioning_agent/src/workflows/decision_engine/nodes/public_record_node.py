"""
Public Record Evaluation Engine
Bankruptcy / liens / hard stop detector with deterministic policy logic.
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.calculators.public_records import classify_public_records
from src.policy.policy_registry import get_active_policy
from src.services.public_record_model.public_record_parser import PublicRecordOutput
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("public_record_engine")
@audit_node(agent_name="decisioning_agent")
def public_record_node(state: LoanApplicationState) -> LoanApplicationState:
    raw_experian = state.get("pi_masked_experian_data")
    public_records = raw_experian.get("publicRecord", [])

    result = PublicRecordOutput(
        **classify_public_records(public_records, get_active_policy().model_dump())
    )
    public_record_data = result.model_dump()
    public_record_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"public_record_data": public_record_data}
