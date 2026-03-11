"""
Underwriting Service

Entry point for running the decisioning workflow.
Accepts an UnderwritingRequest and returns the final decision payload.
"""

import asyncio
import time

from src.core.database import AsyncSessionLocal
from src.core.exceptions import (
    DuplicateRequestInProgressError,
    IdempotencyConflictError,
)
from src.domain.underwriting_models import UnderwritingRequest, UnderwritingResponse
from src.repositories.idempotency_repository import UnderwritingIdempotencyRepository
from src.repositories.service_audit_repository import ServiceAuditRepository
from src.repositories.underwriting_repository import UnderwritingRepository
from src.utils.hash import stable_payload_hash
from src.services.idempotency import resolve_idempotent_response
from src.workflows.decision_flow import build_underwriting_graph


_graph = build_underwriting_graph()


async def _execute_underwriting(request: UnderwritingRequest) -> dict:
    request_payload = request.model_dump(mode="json")
    request_hash = stable_payload_hash(request_payload)
    correlation_id = request.correlation_id or request.application_id
    started_at = time.time()
    response_payload = None
    status = "SUCCESS"
    error_message = None
    idempotency_created = False

    async with AsyncSessionLocal() as session:
        idempotency_repo = UnderwritingIdempotencyRepository(session)
        repo = UnderwritingRepository(session)
        audit_repo = ServiceAuditRepository(session)

        try:
            existing = await idempotency_repo.get(request.application_id)
            try:
                cached_response = resolve_idempotent_response(
                    existing,
                    request.application_id,
                    request_hash,
                )
                if cached_response:
                    response_payload = cached_response
                    status = "IDEMPOTENT_HIT"
                    return cached_response
            except IdempotencyConflictError:
                status = "CONFLICT"
                raise
            except DuplicateRequestInProgressError:
                status = "IN_PROGRESS"
                raise

            await idempotency_repo.create(request.application_id, request_hash)
            idempotency_created = True

            initial_state = {
                "application_id": request.application_id,
                "correlation_id": correlation_id,
                "raw_experian_data": request.raw_experian_data,
                "user_request": {
                    "amount": request.requested_amount,
                    "tenure": request.requested_tenure_months,
                },
                "bank_statement_summary": {
                    "monthly_income": request.monthly_income,
                },
            }

            final_state = _graph.invoke(initial_state)
            response_payload = final_state.get("final_response_payload", {})
            result = UnderwritingResponse.model_validate(response_payload).model_dump()
            response_payload = result

            await repo.save_decision(result)
            await idempotency_repo.mark_completed(request.application_id, result)
            return result
        except Exception as exc:
            error_message = str(exc)
            if idempotency_created:
                await idempotency_repo.mark_failed(request.application_id, str(exc))
            raise
        finally:
            await audit_repo.save_log(
                application_id=request.application_id,
                correlation_id=correlation_id,
                agent_name="decisioning_agent",
                operation_name="underwrite",
                request_payload=request_payload,
                response_payload=response_payload,
                status=status,
                error_message=error_message,
                execution_time_ms=int((time.time() - started_at) * 1000),
            )


def run_underwriting(request: UnderwritingRequest) -> dict:
    """
    Execute the underwriting decision workflow.

    Args:
        request: An UnderwritingRequest containing applicant, credit,
                 and financial data for risk evaluation.

    Returns:
        The final decision response payload as a dict.
    """

    result = asyncio.run(_execute_underwriting(request))
    print("Graph execution result Underwriting:", result)
    return result
