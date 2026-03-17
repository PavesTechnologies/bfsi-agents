from src.utils.audit_decorator import audit_node
from src.workflows.kyc_engine.kyc_state import KYCState, RawKYCRequest

@audit_node(agent_name="kyc_agent")
def normalize_node(state: KYCState) -> KYCState:
    """
    Normalize and standardize incoming KYC data.
    This node serves as the entry point for all KYC processing,
    ensuring that the data is in a consistent format for downstream nodes.
    """

    result: RawKYCRequest = {
        "applicant_id": state["raw_request"].get("applicant_id", "").strip(),
        "full_name": state["raw_request"].get("full_name", "").strip(),
        "dob": str(state["raw_request"].get("dob", "")).strip(),
        "ssn": state["raw_request"].get("ssn", "").strip(),
        "address": {
            "line1": state["raw_request"].get("address", {}).get("line1", "").strip(),
            "line2": state["raw_request"].get("address", {}).get("line2", "").strip(),
            "city": state["raw_request"].get("address", {}).get("city", "").strip(),
            "state": state["raw_request"].get("address", {}).get("state", "").strip(),
            "zip": state["raw_request"].get("address", {}).get("zip", "").strip(),
        },
        "phone": state["raw_request"].get("phone", "").strip(),
        "email": state["raw_request"].get("email", "").strip(),
    }

    # Update the state with the normalized raw_request
    state["raw_request"] = result
    return state
