from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.models.enums import IdempotencyStatus
from src.models.interfaces.kyc_interface.kyc_request_interface import KYCTriggerRequest
from src.repositories.kyc_repo.kyc_repository import KYCRepository
from src.utils.hash_utils import generate_payload_hash
from src.workflows.decision_flow import build_graph
from src.workflows.kyc_engine.kyc_state import RawKYCRequest
# Import your team's Pydantic models

class KYCOrchestratorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KYCRepository(db)
        self.graph = build_graph()

    async def verify_identity(self, payload: KYCTriggerRequest) -> dict:
        """
        Merged logic: Idempotency + Parallel Graph Execution.
        Uses Pydantic models for type safety instead of Dict[str, Any].
        """
        # 1. Generate hash from the model for integrity checks
        payload_dict = payload.model_dump(mode="json")
        payload_hash = generate_payload_hash(payload_dict)

        # 2. Idempotency Check (Domain Rule)
        existing = await self._check_idempotency(payload.idempotency_key, payload_hash)
        if existing:
            return existing

        # 3. Persistence: Create the KYC Case
        kyc_case = await self.repo.create_kyc_case(
            applicant_id=payload.applicant_id,
            payload_hash=payload_hash,
            raw_request_payload=payload_dict
        )

        # 4. Execution: Run the Parallel LangGraph workflow
        result = await self._run_graph_execution(payload)
        print("Graph execution result:", result)  # For debugging; replace with proper logging

        # 5. Finalize: Update DB with results for audit artifacts
        # await self.repo.update_kyc_request_response(
        #     kyc_id=kyc_case.id,
        #     response_payload=result,
        #     status=IdempotencyStatus.SUCCESS
        # )
        # ⭐ NEW — persist identity check
        await self.repo.create_identity_check(
    kyc_id=kyc_case.id,
    applicant_id=payload.applicant_id,
    final_status=result.get("status"),
    risk_payload=result.get("kyc_result"),
)  # 5. Finalize idempotency record
        await self.repo.update_kyc_request_response(
    kyc_id=kyc_case.id,
    response_payload=result,
    status=IdempotencyStatus.SUCCESS
)

        return result

    async def _check_idempotency(self, key: str, current_hash: str) -> dict | None:
        record = await self.repo.get_request_by_idempotency(key)
        if not record:
            return None

        if record.payload_hash != current_hash:
            raise HTTPException(status_code=409, detail="Idempotency key reused with different payload")

        if record.response_status == IdempotencyStatus.PENDING:
            raise HTTPException(status_code=202, detail={"kyc_status": "PENDING", "kyc_id": str(record.kyc_id)})

        return record.response_payload

    async def _run_graph_execution(self, payload: KYCTriggerRequest) -> dict:
        """Maps Pydantic model to RawKYCRequest and runs the graph."""
        # Mapping model attributes to the internal KYCState shape
        raw_req: RawKYCRequest = {
            "applicant_id": payload.applicant_id,
            "full_name": payload.full_name,
            "dob": payload.dob,
            "ssn": payload.ssn,
            "address": {
                "line1": payload.address.line1,
                "line2": payload.address.line2 or "",
                "city": payload.address.city,
                "state": payload.address.state,
                "zip": payload.address.zip
            },
            "phone": payload.phone,
            "email": payload.email
        }

        initial_state = {
            "raw_request": raw_req,
            "hard_stop": False,
            "parallel_tasks_completed": [],
            "node_execution_times": {}
        }

        # Parallel fan-out execution
        final_state = await self.graph.ainvoke(initial_state)

        return {
            "applicant_id": payload.applicant_id,
            "status": final_state.get("risk_decision", {}).get("final_status"),
            "kyc_result": final_state.get("risk_decision"),
            "audit": {
                "tasks": final_state.get("parallel_tasks_completed"),
                "performance": final_state.get("node_execution_times")
            }
        }