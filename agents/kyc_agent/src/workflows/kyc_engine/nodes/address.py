"""
Address Verification Node
"""

from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
from src.core.telemetry import track_node
from src.services.identity_service import IdentityService
from src.workflows.kyc_engine.kyc_state import KYCState


@track_node("address")
def address_node(state: KYCState) -> KYCState:
    """
    Thin node: Orchestrates the sequence between Adapter and Service.
    Uses Experian credit report data for address verification.
    """
    req = state["raw_request"]

    # 1. Adapter call (External Interaction)
    adapter = MockExperianAdapter()
    experian_data = adapter.get_credit_report(
        {
            "firstName": req["full_name"].split()[0],
            "lastName": req["full_name"].split()[-1],
            "street1": req["address"]["line1"],
            "city": req["address"]["city"],
            "state": req["address"]["state"],
            "zip": req["address"]["zip"],
            "ssn": req["ssn"],
        }
    )

    # 2. Service call (Business Logic Delegation)
    address_verification_state = IdentityService.process_address_verification(
        req, experian_data
    )

    return {
        "address_verification": address_verification_state,
    }
