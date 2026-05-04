from src.adapters.mock_adapters.mock_video_kyc_adapter import MockVideoKYCAdapter
from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState


@track_node("video_kyc")
@audit_node(agent_name="kyc_agent")
async def video_kyc_node(state: IndianKYCState) -> IndianKYCState:
    req = state["raw_request"]
    aadhaar_number = req.get("aadhaar_number", "")
    aadhaar_prefix = aadhaar_number[:4] if len(aadhaar_number) >= 4 else ""

    adapter = MockVideoKYCAdapter()
    session = adapter.initiate_session(req["applicant_id"])
    video_state = adapter.get_session_result(session["session_id"], aadhaar_prefix)

    return {"video_kyc": video_state}
