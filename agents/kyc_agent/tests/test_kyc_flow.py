from src.workflows.kyc_engine.kyc_state import KYCState
from src.workflows.kyc_engine.orchestrator import execute_kyc


def run_demo():
    state = KYCState(
        application_id="APP-123",
        execution_id="RUN-1",
        applicant_data={"full_name": "John Doe"}
    )

    result = execute_kyc(state)

    print("\nFINAL STATUS:", result.status)
    print("DECISION:", result.decision)
    print("FLAGS:", result.flags)

    print("\n--- HISTORY ---")
    for h in result.history:
        print(h.event, "|", h.node)


if __name__ == "__main__":
    run_demo()
