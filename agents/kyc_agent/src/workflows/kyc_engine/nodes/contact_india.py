from src.adapters.mock_adapters.mock_contact_india_adapter import MockContactIndiaAdapter
from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState


@track_node("contact_india")
@audit_node(agent_name="kyc_agent")
def contact_india_node(state: IndianKYCState) -> IndianKYCState:
    req = state["raw_request"]

    adapter = MockContactIndiaAdapter()
    contact_state = adapter.verify({
        "phone": req.get("phone", ""),
        "upi_handle": req.get("upi_handle"),
    })

    return {"contact_india": contact_state}
