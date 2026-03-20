"""
Workflow orchestrator.

Entry point for running the disbursement workflow.
Accepts a ``DisbursementRequest`` and returns the final receipt.
"""

import asyncio
import time

from src.core.database import AsyncSessionLocal
from src.core.exceptions import (
    DuplicateRequestInProgressError,
    IdempotencyConflictError,
)
from src.domain.entities import DisbursementRequest
from src.repositories.idempotency_repository import DisbursementIdempotencyRepository
from src.repositories.disbursement_repository import DisbursementRepository
from src.repositories.disbursement_transition_repository import (
    DisbursementTransitionRepository,
)
from src.repositories.service_audit_repository import ServiceAuditRepository
from src.services.disbursement_transitions import derive_transition_history
from src.services.idempotency import resolve_idempotent_response
from src.utils.hash import stable_payload_hash
from src.workflows.decision_flow import build_disbursement_graph

_graph = build_disbursement_graph()


async def _execute_disbursement(request: DisbursementRequest) -> dict:
    request_payload = request.model_dump(mode="json")
    request_hash = stable_payload_hash(request_payload)
    correlation_id = request.correlation_id or request.application_id
    started_at = time.time()
    response_payload = None
    status = "SUCCESS"
    error_message = None
    idempotency_created = False

    async with AsyncSessionLocal() as session:
        idempotency_repo = DisbursementIdempotencyRepository(session)
        repo = DisbursementRepository(session)
        transition_repo = DisbursementTransitionRepository(session)
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
                "decision": request.decision,
                "risk_tier": request.risk_tier,
                "risk_score": request.risk_score,
                "disbursement_status": "PENDING",
            }

            if request.decision == "APPROVE" and request.loan_details:
                initial_state["approved_amount"] = request.loan_details.approved_amount
                initial_state["approved_tenure_months"] = request.loan_details.approved_tenure_months
                initial_state["interest_rate"] = request.loan_details.interest_rate
                initial_state["disbursement_amount"] = request.loan_details.disbursement_amount
                initial_state["explanation"] = request.loan_details.explanation
            elif request.decision == "COUNTER_OFFER" and request.counter_offer:
                initial_state["counter_offer"] = request.counter_offer.model_dump()
                initial_state["selected_option_id"] = request.selected_option_id
            elif request.decision == "DECLINE":
                initial_state["explanation"] = request.decline_reason

            final_state = _graph.invoke(initial_state)
            receipt = final_state.get("disbursement_receipt", {})
            response_payload = receipt
            await repo.save_record(receipt)
            for transition in derive_transition_history(final_state):
                await transition_repo.save_transition(
                    application_id=request.application_id,
                    correlation_id=correlation_id,
                    from_status=transition["from_status"],
                    to_status=transition["to_status"],
                    reason=transition["reason"],
                    transition_metadata=transition["transition_metadata"],
                )
            await idempotency_repo.mark_completed(request.application_id, receipt)
            return receipt
        except Exception as exc:
            error_message = str(exc)
            if idempotency_created:
                await idempotency_repo.mark_failed(request.application_id, str(exc))
            raise
        finally:
            await audit_repo.save_log(
                application_id=request.application_id,
                correlation_id=correlation_id,
                agent_name="disbursment_agent",
                operation_name="disburse",
                request_payload=request_payload,
                response_payload=response_payload,
                status=status,
                error_message=error_message,
                execution_time_ms=int((time.time() - started_at) * 1000),
            )


def run_disbursement(request: DisbursementRequest) -> dict:
    """
    Execute the disbursement workflow and persist the final receipt.
    """
    return asyncio.run(_execute_disbursement(request))
