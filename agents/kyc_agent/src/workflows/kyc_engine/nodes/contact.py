from src.core.telemetry import track_node
from src.services.identity_service import IdentityService
from src.workflows.kyc_engine.kyc_state import KYCState
from src.utils.audit_decorator import audit_node


@track_node("contact")
@audit_node(agent_name="kyc_agent")
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
