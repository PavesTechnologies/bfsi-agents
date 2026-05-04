from src.adapters.mock_adapters.mock_ckyc_adapter import MockCKYCAdapter
from src.core.telemetry import track_node
from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState


@track_node("ckyc_upload")
@audit_node(agent_name="kyc_agent")
async def ckyc_upload_node(state: IndianKYCState) -> IndianKYCState:
    req = state["raw_request"]
    aadhaar_number = req.get("aadhaar_number", "")
    aadhaar_prefix = aadhaar_number[:4] if len(aadhaar_number) >= 4 else ""

    adapter = MockCKYCAdapter()
    ckyc_state = adapter.upload(
        applicant_id=req["applicant_id"],
        aadhaar_prefix=aadhaar_prefix,
        kyc_payload={
            "aadhaar_verification": state.get("aadhaar_verification"),
            "pan_verification": state.get("pan_verification"),
            "video_kyc": state.get("video_kyc"),
        },
    )

    return {"ckyc": ckyc_state}
