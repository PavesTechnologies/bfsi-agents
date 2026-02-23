from typing import Dict, Any
from src.workflows.decision_flow import build_graph
from src.workflows.kyc_engine.kyc_state import RawKYCRequest, Address

class KYCOrchestratorService:
    def __init__(self):
        self.graph = build_graph()

    async def run_kyc_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates the KYC process by initializing state and running the graph.
        Aligns with PRD Section 4: System Positioning.
        """
        # 1. Map raw JSON input to Domain Models (PRD 5.1)
        # Note: In a real app, use Pydantic for validation here
        address_data = input_data.get("address", {})
        print(f"Received address data: {address_data}")
        raw_request:RawKYCRequest={
            "applicant_id":input_data.get("applicant_id"),
            "full_name":input_data.get("full_name"),
            "dob":input_data.get("dob"),
            "ssn":input_data.get("ssn"),
            "address":{
                "line1":address_data.get("line1",""),
                "line2":address_data.get("line2",""),
                "city":address_data.get("city",""),
                "state":address_data.get("state",""),
                "zip":address_data.get("zip","")
            },
            "phone":input_data.get("phone"),
            "email":input_data.get("email")
        }

        print(f"Received raw request: {raw_request}")

        # 2. Initialize KYCState
        initial_state = {
            "raw_request": raw_request,
            "hard_stop": False,
            "parallel_tasks_completed": [],
            "node_execution_times": {}
        }

        # 3. Execute Graph (Async)
        # LangGraph handles the parallel fan-out of ssn, address, face, and aml
        final_state = await self.graph.ainvoke(initial_state)

        print(f"Final state  graph execution")
        # 4. Return structured response (PRD 9.1)
        return {
            "applicant_id": raw_request["applicant_id"],
            "status": final_state.get("risk_decision", {}).get("final_status"),
            "kyc_result": final_state.get("risk_decision"),
            "audit": {
                "tasks": final_state.get("parallel_tasks_completed"),
                "performance": final_state.get("node_execution_times")
            }
        }