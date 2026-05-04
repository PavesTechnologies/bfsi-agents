from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.india_kyc_state import IndianKYCState, RawIndianKYCRequest


@audit_node(agent_name="kyc_agent")
def normalize_india_node(state: IndianKYCState) -> IndianKYCState:
    """Normalise and standardise incoming Indian KYC request fields."""
    raw = state["raw_request"]

    result: RawIndianKYCRequest = {
        "applicant_id": raw.get("applicant_id", "").strip(),
        "full_name": raw.get("full_name", "").strip(),
        "dob": str(raw.get("dob", "")).strip(),
        "aadhaar_number": raw.get("aadhaar_number", "").replace(" ", "").strip(),
        "aadhaar_otp": raw.get("aadhaar_otp"),
        "pan_number": raw.get("pan_number", "").upper().strip(),
        "address": {
            "line1": raw.get("address", {}).get("line1", "").strip(),
            "line2": raw.get("address", {}).get("line2", "").strip(),
            "city": raw.get("address", {}).get("city", "").strip(),
            "state": raw.get("address", {}).get("state", "").strip(),
            "pincode": raw.get("address", {}).get("pincode", "").strip(),
        },
        "phone": raw.get("phone", "").strip(),
        "email": raw.get("email", "").strip(),
    }

    state["raw_request"] = result
    return state
