from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import KYCState
from src.services.identity_service import IdentityService

@track_node("contact")
def contact_node(state: KYCState) -> KYCState:
    """
    Orchestrates validation of phone and email metadata.
    """
    req = state["raw_request"]
    
    # Logic delegation to service layer
    contact_state = IdentityService.process_contact_verification(req)
    
    return {
        "contact_verification": contact_state,
    }