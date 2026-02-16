# src/services/orchestrator.py

from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.repositories.kyc_attempt_repository import KYCAttemptRepository
from src.workflows.decision_flow import build_graph
from src.repositories.idempotency_repository import RedisIdempotencyRepository

_graph = build_graph()


async def run_kyc(request: Request, body):

    application_id = request.state.application_id
    idempotency_key = request.state.idempotency_key
    payload_hash = request.state.payload_hash

    async with get_async_session() as session:
        repo = KYCAttemptRepository(session)

        existing = await repo.get_latest_attempt(
            application_id, idempotency_key
        )

        if existing:
            if existing.payload_hash != payload_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key reused with different payload",
                )

            if existing.status in ["PASSED", "FAILED", "REVIEW"]:
                # Replay
                return {
                    "kyc_status": existing.status,
                    "replayed": True,
                }

            # If still PENDING
            raise HTTPException(
                status_code=409,
                detail="KYC attempt already in progress",
            )

        # New attempt
        max_version = await repo.get_max_attempt_version(application_id)
        attempt = await repo.create_attempt(
            application_id,
            idempotency_key,
            payload_hash,
            max_version + 1,
        )

    # Run workflow OUTSIDE transaction
    final_state = _graph.invoke(
        {
            "context": {
                "application_id": str(application_id),
                "applicant_data": body.applicant_data,
            },
            "retries": 0,
        }
    )

    decision_output = {
        "final_status": final_state["context"].get("decision"),
        "confidence_score": 0.95,
    }

    async with get_async_session() as session:
        repo = KYCAttemptRepository(session)

        await repo.create_risk_decision(attempt.id, decision_output)
        await repo.update_attempt_status(attempt.id, decision_output["final_status"])

    # Release lock
    redis_repo: RedisIdempotencyRepository = request.app.state.redis_repo
    await redis_repo.release_lock(idempotency_key)

    return {
        "kyc_status": decision_output["final_status"],
        "confidence_score": decision_output["confidence_score"],
    }
