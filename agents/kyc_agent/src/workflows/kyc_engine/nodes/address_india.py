from src.adapters.mock_adapters.mock_address_india_adapter import MockAddressIndiaAdapter
from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState


@track_node("address_india")
@audit_node(agent_name="kyc_agent")
async def address_india_node(state: IndianKYCState) -> IndianKYCState:
    req = state["raw_request"]

    adapter = MockAddressIndiaAdapter()
    address_state = adapter.verify(req.get("address", {}))

    return {"address_india": address_state}
