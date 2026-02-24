

from src.workflows.kyc_engine.kyc_state import KYCState
from src.workflows.kyc_engine.kyc_state import RawKYCRequest


def normalize_node(state: KYCState) -> KYCState:
    """
    Normalize and standardize incoming KYC data.
    This node serves as the entry point for all KYC processing, ensuring that the data is in a consistent format for downstream nodes.
    """
    # For demonstration, we'll just pass through the state without modification.
    # In a real implementation, this would include data cleaning, formatting, and enrichment logic.
    # result:RawKYCRequest={
    #     "applicant_id": "user_9988",
    #     "full_name": "John Quincy Public",
    #     "dob": "1985-05-15",
    #     "ssn": "666451234",
    #     "address": {
    #         "line1": "1600 Pennsylvania Avenue NW",
    #         "city": "Washington",
    #         "state": "DC",
    #         "zip": "20500"
    #     },
    #     "phone": "+12024561111",
    #     "email": "jq.public@example.com"
    #     }

    result:RawKYCRequest={
        "applicant_id": state["raw_request"].get("applicant_id", "").strip(),
        "full_name": state["raw_request"].get("full_name", "").strip(),
        "dob": str(state["raw_request"].get("dob", "")).strip(),
        "ssn": state["raw_request"].get("ssn", "").strip(),
        "address": {
            "line1": state["raw_request"].get("address", {}).get("line1", "").strip(),
            "line2": state["raw_request"].get("address", {}).get("line2", "").strip(),
            "city": state["raw_request"].get("address", {}).get("city", "").strip(),
            "state": state["raw_request"].get("address", {}).get("state", "").strip(),
            "zip": state["raw_request"].get("address", {}).get("zip", "").strip()
        },
        "phone": state["raw_request"].get("phone", "").strip(),
        "email": state["raw_request"].get("email", "").strip()
    }
    
    

    
    # Update the state with the normalized raw_request
    state["raw_request"] = result
    return state