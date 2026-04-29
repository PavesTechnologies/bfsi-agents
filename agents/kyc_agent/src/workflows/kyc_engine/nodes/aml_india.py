from src.adapters.mock_adapters.mock_aml_india_adapter import MockAMLIndiaAdapter
from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState


@track_node("aml_india")
@audit_node(agent_name="kyc_agent")
async def aml_india_node(state: IndianKYCState) -> IndianKYCState:
    req = state["raw_request"]

    adapter = MockAMLIndiaAdapter()
    aml_state = adapter.screen({
        "full_name": req["full_name"],
        "dob": req["dob"],
        "aadhaar_number": req["aadhaar_number"],
        "pan_number": req["pan_number"],
    })

    return {"aml_india": aml_state}
