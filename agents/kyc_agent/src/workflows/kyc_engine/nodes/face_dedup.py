from src.adapters.mock_adapters.mock_face_dedup_adapter import MockFaceDedupAdapter
from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState


@track_node("face_dedup")
@audit_node(agent_name="kyc_agent")
async def face_dedup_node(state: IndianKYCState) -> IndianKYCState:
    req = state["raw_request"]
    aadhaar_number = req.get("aadhaar_number", "")
    aadhaar_prefix = aadhaar_number[:4] if len(aadhaar_number) >= 4 else ""

    adapter = MockFaceDedupAdapter()
    dedup_state = adapter.check_duplicate(req["applicant_id"], aadhaar_prefix)

    return {"face_dedup": dedup_state}
