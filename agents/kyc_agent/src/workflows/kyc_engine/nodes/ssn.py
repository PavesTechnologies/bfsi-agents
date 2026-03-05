from langchain_core.runnables import RunnableConfig

from src.adapters.mock_adapters.mock_experian_adapter import MockExperianAdapter
from src.core.telemetry import track_node
from src.services.identity_service import IdentityService
from src.workflows.kyc_engine.kyc_state import KYCState


@track_node("ssn")
async def ssn_node(state: KYCState, config: RunnableConfig) -> KYCState:
    """
    Thin node: Orchestrates the sequence between Adapter and Service (Architecture Section).
    """  # noqa: E501
    # start_time = time.time()
    req = state["raw_request"]  # Accessing typed RawKYCRequest
    db = config["configurable"].get("db")
    kyc_id = config["configurable"].get("kyc_id")
    # 1. Adapter call (External Interaction)
    # Note: Adapter still needs primitive dict until we update its signature
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
    ssn_validation_state = IdentityService.process_ssn_verification(req, experian_data)

    print(f"SSN Node Output: {ssn_validation_state}")  # Debug log for output state

    return {
        "ssn_validation": ssn_validation_state,
        "raw_experian_data": experian_data,
        # "parallel_tasks_completed": ["ssn"],
        # "node_execution_times": {"ssn": time.time() - start_time}
    }
