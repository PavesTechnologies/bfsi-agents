

from src.workflows.kyc_engine.kyc_state import KYCState
from src.workflows.kyc_engine.kyc_state import RawKYCRequest


def normalize_node(state: KYCState) -> KYCState:
    """
    Normalize and standardize incoming KYC data.
    This node serves as the entry point for all KYC processing, ensuring that the data is in a consistent format for downstream nodes.
    """
    # For demonstration, we'll just pass through the state without modification.
    # In a real implementation, this would include data cleaning, formatting, and enrichment logic.
    
    result:RawKYCRequest={
        "applicant_id": "user_9988",
        "full_name": "John Quincy Public",
        "dob": "1985-05-15",
        "ssn": "666451234",
        "address": {
            "line1": "1600 Pennsylvania Avenue NW",
            "city": "Washington",
            "state": "DC",
            "zip": "20500"
        },
        "phone": "+12024561111",
        "email": "jq.public@example.com"
        }

    
    # Update the state with the normalized raw_request
    state["raw_request"] = result
    return state