# src/services/india_orchestrator.py

import uuid

from fastapi import Request

from src.core.database import AsyncSessionLocal
from src.models.enums import FinalDecision, IdempotencyStatus, KYCStatus
from src.repositories.kyc_repo.kyc_repository import KYCRepository
from src.utils.hash_utils import generate_payload_hash
from src.workflows.india_decision_flow import build_india_graph

_graph = build_india_graph()

# Graph outputs PASS / FAIL / NEEDS_HUMAN_REVIEW
# DB kyc_cases.status  → KYCStatus  (PASSED / FAILED / REVIEW)
# DB risk_decisions.final_status → FinalDecision  (PASS / REVIEW / FAIL)
_KYC_STATUS_MAP = {
    "PASS": KYCStatus.PASSED,
    "FAIL": KYCStatus.FAILED,
    "NEEDS_HUMAN_REVIEW": KYCStatus.REVIEW,
}

_FINAL_DECISION_MAP = {
    "PASS": FinalDecision.PASS,
    "FAIL": FinalDecision.FAIL,
    "NEEDS_HUMAN_REVIEW": FinalDecision.REVIEW,
}


async def run_kyc_india(request: Request, body):
    application_id = body.application_id          # UUID object — matches DB uuid column
    application_id_str = str(application_id)
    idempotency_key = request.headers.get("X-Idempotency-Key") or str(uuid.uuid4())
    payload_hash = generate_payload_hash(body.model_dump(mode="json"))

    async with AsyncSessionLocal() as db:
        repo = KYCRepository(db)

        # --- Idempotency check ---
        existing = await repo.get_request_by_idempotency(idempotency_key)
        if existing:
            if existing.payload_hash != payload_hash:
                return {"detail": "Idempotency key reused with different payload"}
            return existing.response_payload

        # --- Create KYC case ---
        kyc_case = await repo.create_kyc_case(
            applicant_id=application_id,
            payload_hash=payload_hash,
            raw_request_payload=body.model_dump(mode="json"),
        )

        # --- Mark request as in-flight ---
        await repo.create_kyc_request(
            kyc_id=kyc_case.id,
            idempotency_key=idempotency_key,
            payload_hash=payload_hash,
            response_payload={},
        )

        await db.commit()

        # --- Run the India KYC graph ---
        initial_state = {
            "raw_request": {
                "applicant_id": application_id_str,
                **body.applicant_data,
            }
        }

        config = {
            "configurable": {
                "thread_id": application_id_str,
                "db": db,
                "kyc_id": str(kyc_case.id),
            }
        }

        final_state = await _graph.ainvoke(initial_state, config=config)

        risk = final_state.get("risk_decision") or {}
        final_status_str = risk.get("final_status", "FAIL")

        kyc_status = _KYC_STATUS_MAP.get(final_status_str, KYCStatus.FAILED)
        # Normalise for risk_decisions.final_status enum (PASS / REVIEW / FAIL only)
        db_final_decision = _FINAL_DECISION_MAP.get(final_status_str, FinalDecision.FAIL)

        response_payload = {
            "kyc_status": final_status_str,
            "confidence_score": risk.get("confidence_score", 0.0),
            "decision_explanation": final_state.get("decision_explanation"),
            "ckyc_id": (final_state.get("ckyc") or {}).get("ckyc_id"),
            "hard_fail_rules": risk.get("hard_fail_rules", []),
            "soft_flags": risk.get("soft_flags", []),
        }

        # Build a DB-safe risk dict (final_status mapped to the DB enum value)
        db_risk = {**risk, "final_status": db_final_decision.value}

        # --- Persist results ---
        await repo.update_kyc_case_response(kyc_id=kyc_case.id, status=kyc_status)
        await repo.save_risk_decision(kyc_id=str(kyc_case.id), decision_data=db_risk)
        await repo.update_kyc_request_response(
            kyc_id=kyc_case.id,
            response_payload=response_payload,
            status=IdempotencyStatus.SUCCESS,
        )

        await db.commit()

        return response_payload
