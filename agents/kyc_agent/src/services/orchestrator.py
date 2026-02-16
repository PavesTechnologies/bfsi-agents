# src/services/orchestrator.py

from fastapi import Request, HTTPException
from src.utils.migration_database import SessionLocal
from src.repositories.kyc_attempt_repository import KYCAttemptRepository
from src.models.enums import FinalDecision, KYCStatus
from src.workflows.decision_flow import build_graph

_graph = build_graph()


async def run_kyc(request: Request, body):

    application_id = request.state.application_id
    idempotency_key = request.state.idempotency_key
    payload_hash = request.state.payload_hash

    db = SessionLocal()
    repo = KYCAttemptRepository(db)

    try:
        existing = repo.get_latest_attempt(application_id, idempotency_key)

        if existing:
            if existing.payload_hash != payload_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key reused with different payload",
                )

            if existing.status != KYCStatus.PENDING:
                return {
                    "kyc_status": existing.status.value,
                    "confidence_score": existing.confidence_score,
                    "replayed": True,
                }

            raise HTTPException(
                status_code=409,
                detail="KYC attempt already in progress",
            )

        max_version = repo.get_max_attempt_version(application_id)

        attempt = repo.create_attempt(
            application_id,
            idempotency_key,
            payload_hash,
            max_version + 1,
        )

        # Run workflow
        final_state = _graph.invoke(
            {
                "context": {
                    "application_id": str(application_id),
                    "applicant_data": body.applicant_data,
                },
                "retries": 0,
            }
        )

        decision_value = final_state["context"].get("decision")

        final_decision = FinalDecision[decision_value]

        decision_output = {
            "final_status": final_decision,
            "confidence_score": 0.95,
            "reason": final_state["context"].get("reason"),
        }

        repo.create_risk_decision(attempt.id, decision_output)
        repo.update_attempt_status(
            attempt.id,
            final_decision,
            decision_output["confidence_score"],
        )

        return {
            "kyc_status": final_decision.value,
            "confidence_score": decision_output["confidence_score"],
        }

    finally:
        db.close()
        redis_repo = request.app.state.redis_repo
        await redis_repo.release_lock(idempotency_key)
