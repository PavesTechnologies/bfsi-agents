from fastapi import HTTPException
from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enums import IdempotencyStatus
from src.models.interfaces.kyc_interface.kyc_request_interface import KYCTriggerRequest
from src.repositories.kyc_repo.kyc_repository import KYCRepository
from src.utils.hash_utils import generate_payload_hash
from src.workflows.decision_flow import build_graph
from src.workflows.kyc_engine.kyc_state import RawKYCRequest
import json
from src.repositories.langgraph_failed_thread_repository import KYCFailedThreadRepository
# Import your team's Pydantic models


class KYCOrchestratorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KYCRepository(db)
        self.graph = build_graph()
        self.failed_repo = KYCFailedThreadRepository(db) 

    async def verify_identity(self, payload: KYCTriggerRequest) -> dict:
        """
        Merged logic: Idempotency + Parallel Graph Execution.
        Uses Pydantic models for type safety instead of Dict[str, Any].
        """
        print("KYC Orchestrator Service: Triggered KYC verification")

        # 1. Generate hash from the model for integrity checks
        payload_dict = payload.model_dump(mode="json")
        payload_hash = generate_payload_hash(payload_dict)

        print("KYC Orchestrator Service: Generated payload hash")

        # 2. Idempotency Check (Domain Rule)
        existing = await self._check_idempotency(payload.idempotency_key, payload_hash)
        if existing:
            return existing

        # 3. Persistence: Create the KYC Case
        kyc_case = await self.repo.create_kyc_case(
            applicant_id=payload.applicant_id,
            payload_hash=payload_hash,
            raw_request_payload=payload_dict,
        )

        print(f"Created KYC Case with ID: {kyc_case.id}")  # Debug log for created case

        await self.db.flush()  # Commit to generate KYC ID for logging in adapters

        config = {
                    "db": self.db,
                    "kyc_id": kyc_case.id,
                    "applicant_id": payload.applicant_id,
                }

        # 4. Execution: Run the Parallel LangGraph workflow
        result = await self._run_graph_execution(payload, config=config)
        print(
            "Graph execution result:", result
        )  # For debugging; replace with proper logging

        await self.db.commit()
        # 5. Finalize: Update DB with results for audit artifacts
        # await self.repo.update_kyc_request_response(
        #     kyc_id=kyc_case.id,
        #     response_payload=result,
        #     status=IdempotencyStatus.SUCCESS
        # )
        # ⭐ NEW — persist identity check
        kyc_result = result.get("kyc_result", {})
        ssn_snapshot = kyc_result.get("ssn_risk_snapshot", {})
        await self.repo.create_identity_check(
            kyc_id=kyc_case.id,
            applicant_id=payload.applicant_id,
            final_status=kyc_result.get("final_status"),
            aggregated_score=kyc_result.get("aggregated_score"),
            hard_fail_triggered=kyc_result.get("hard_fail_triggered"),
            # 🔹 SSN flags
            ssn_valid=ssn_snapshot.get("ssn_valid"),
            ssn_plausible=ssn_snapshot.get("ssn_plausible"),
            name_ssn_match=ssn_snapshot.get("name_ssn_match"),
            dob_ssn_match=ssn_snapshot.get("dob_ssn_match"),
            deceased_flag=ssn_snapshot.get("deceased_flag"),
            # 🔹 JSON payloads
            ssn_risk_snapshot=ssn_snapshot,
            decision_rules_snapshot=kyc_result.get("decision_rules_snapshot"),
            model_versions=kyc_result.get("model_versions"),
            audit_payload=result.get("audit"),
        )  # 5. Finalize idempotency record
        await self.repo.update_kyc_request_response(
            kyc_id=kyc_case.id,
            response_payload=result,
            status=IdempotencyStatus.SUCCESS,
        )


        return result

    async def _check_idempotency(self, key: str, current_hash: str) -> dict | None:
        record = await self.repo.get_request_by_idempotency(key)
        if not record:
            return None

        if record.payload_hash != current_hash:
            raise HTTPException(
                status_code=409, detail="Idempotency key reused with different payload"
            )

        if record.response_status == IdempotencyStatus.PENDING:
            raise HTTPException(
                status_code=202,
                detail={"kyc_status": "PENDING", "kyc_id": str(record.kyc_id)},
            )

        return record.response_payload

    async def _run_graph_execution(self, payload: KYCTriggerRequest, config) -> dict:
        application_id = payload.applicant_id

        # ✅ Always build input state from payload
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
                "zip": payload.address.zip,
            },
            "phone": payload.phone,
            "email": payload.email,
        }

        input_state = {
            "raw_request": raw_req,
            "hard_stop": False,
            "parallel_tasks_completed": [],
            "node_execution_times": {},
        }

        # 🔁 Check failed thread — reuse thread_id if resuming, else create fresh
        failed_record = await self.failed_repo.get_failed_thread(application_id)

        if failed_record:
            print("🔁 Resuming failed workflow")
            thread_id = failed_record.thread_id  # ✅ reuse old thread_id for checkpoint lookup
        else:
            print("🆕 Starting fresh workflow")
            thread_id = f"kyc_{application_id}"

        try:
            final_state = await self.graph.ainvoke(
                input_state,  # ✅ always pass input — never None
                config=RunnableConfig(
                    configurable={
                        "db": self.db,
                        "kyc_id": config["kyc_id"],
                        "applicant_id": config["applicant_id"],
                        "thread_id": thread_id,
                    }
                ),
            )

            await self.failed_repo.delete_failed_thread(application_id)

        except Exception as e:
            await self.failed_repo.save_failure(
                application_id=application_id,
                thread_id=thread_id,
                failed_node="unknown",
                error_message=str(e),
            )
            raise e

        return {
            "applicant_id": payload.applicant_id,
            "status": final_state.get("risk_decision", {}).get("final_status"),
            "kyc_result": final_state.get("risk_decision"),
            "final_explanation": final_state.get("decision_explanation"),
            "audit": {
                "tasks": final_state.get("parallel_tasks_completed"),
                "performance": final_state.get("node_execution_times"),
            },
            "raw_experian_data": final_state.get("raw_experian_data"),
        }