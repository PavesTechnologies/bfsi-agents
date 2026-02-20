

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
    "applicant_id": "a9f3d7e2-6b4a-4c9f-9d2a-3f1c8b7e12ab",
    "full_name": "Ajay Kumar Bhukya",
    "dob": "1995-08-14",
    "ssn": "732549812",
    "address": {
        "line1": "221B Residency Apartments",
        "line2": "Madhapur",
        "city": "Hyderabad",
        "state": "Telangana",
        "zip": "500081"
    },
    "phone": "+91-9876543210",
    "email": "ajay.bhukya@example.com"
    }
    
    # Update the state with the normalized raw_request
    state["raw_request"] = result
    return state