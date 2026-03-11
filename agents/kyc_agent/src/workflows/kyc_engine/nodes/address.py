"""
Address Verification Node
"""

from langchain_core.runnables import RunnableConfig

from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
from src.core.telemetry import track_node
from src.services.identity_service import IdentityService
from src.workflows.kyc_engine.kyc_state import KYCState
from src.utils.audit_decorator import audit_node


@track_node("address")
@audit_node(agent_name="kyc_agent")
async def address_node(state: KYCState, config: RunnableConfig) -> KYCState:
    """
    Thin node: Orchestrates the sequence between Adapter and Service.
    Uses Experian credit report data for address verification.
    """
    req = state["raw_request"]
    db = config["configurable"].get("db")
    kyc_id = config["configurable"].get("kyc_id")

    # 1. Adapter call (External Interaction)
    adapter = MockExperianAdapter()
    experian_data = await adapter.get_credit_report(
        {
            "firstName": req["full_name"].split()[0],
            "lastName": req["full_name"].split()[-1],
            "street1": req["address"]["line1"],
            "city": req["address"]["city"],
            "state": req["address"]["state"],
            "zip": req["address"]["zip"],
            "ssn": req["ssn"],
        },
        db=db,
        kyc_id=kyc_id,
    )

    # 2. Service call (Business Logic Delegation)
    address_verification_state = IdentityService.process_address_verification(
        req, experian_data
    )

    return {
        "address_verification": address_verification_state,
    }
