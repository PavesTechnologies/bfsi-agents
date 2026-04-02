"""
Underwriting Service

Entry point for running the decisioning workflow.
Accepts an UnderwritingRequest and returns the canonical decision payload.
"""

import time

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    DuplicateRequestInProgressError,
    IdempotencyConflictError,
)
from src.core.versioning import get_runtime_versions
from src.domain.audit.narrative_builder import build_audit_narrative
from src.domain.underwriting_models import UnderwritingRequest
from src.policy.policy_loader import load_underwriting_policy
from src.policy.versioning import build_policy_version_metadata
from src.repositories.idempotency_repository import UnderwritingIdempotencyRepository
from src.repositories.langgraph_failed_th_repository import (
    DecisioningFailedThreadRepository,
)
from src.repositories.service_audit_repository import ServiceAuditRepository
from src.repositories.underwriting_repository import UnderwritingRepository
from src.services.idempotency import resolve_idempotent_response
from src.utils.hash import stable_payload_hash


class UnderwritingService:
    def __init__(self, db: AsyncSession):
        from src.workflows.decision_flow import build_underwriting_graph

        self.db = db
        self.failed_thread_repo = DecisioningFailedThreadRepository(db)
        self.idempotency_repo = UnderwritingIdempotencyRepository(db)
        self.service_audit_repo = ServiceAuditRepository(db)
        self.underwriting_repo = UnderwritingRepository(db)
        self.graph = build_underwriting_graph()

    async def execute_underwriting(
        self,
        request: UnderwritingRequest,
        correlation_id: str | None = None,
    ) -> dict:
        """
        Execute underwriting workflow and save decision to database.

        Handles:
        - APPROVE: Complete loan offer with terms
        - DECLINE: Rejection with reasoning
        - COUNTER_OFFER: Alternative loan terms
        """
        start_time = time.time()
        request_payload = request.model_dump()
        request_hash = stable_payload_hash(request_payload)
        response_payload: dict | None = None
        status = "SUCCESS"
        error_message: str | None = None
        started_processing = False
        thread_id = f"underwriting_{request.application_id}"

        try:
            existing_record = await self.idempotency_repo.get(request.application_id)
            cached_response = resolve_idempotent_response(
                existing_record,
                request.application_id,
                request_hash,
            )
            if cached_response is not None:
                response_payload = cached_response
                return cached_response

            if existing_record and existing_record.status == "FAILED":
                await self.idempotency_repo.reset_processing(
                    request.application_id,
                    request_hash,
                )
            elif not existing_record:
                try:
                    await self.idempotency_repo.create(
                        request.application_id,
                        request_hash,
                    )
                except IntegrityError:
                    existing_record = await self.idempotency_repo.get(request.application_id)
                    cached_response = resolve_idempotent_response(
                        existing_record,
                        request.application_id,
                        request_hash,
                    )
                    if cached_response is not None:
                        response_payload = cached_response
                        return cached_response
                    raise DuplicateRequestInProgressError(request.application_id)

            started_processing = True

            failed_app = await self.failed_thread_repo.get_failed_thread(
                request.application_id
            )
            if failed_app:
                thread_id = failed_app.thread_id
                print("Resuming failed thread:", thread_id)
            else:
                print("New workflow for application:", request.application_id)

            config = {"configurable": {"thread_id": thread_id}}
            policy = load_underwriting_policy()
            initial_state = {
                "application_id": request.application_id,
                "correlation_id": correlation_id,
                "policy_metadata": {
                    **policy.bank.model_dump(),
                    **build_policy_version_metadata(policy),
                },
                "version_metadata": get_runtime_versions(),
                "raw_experian_data": request.raw_experian_data,
                "user_request": {
                    "amount": request.requested_amount,
                    "tenure": request.requested_tenure_months,
                },
                "bank_statement_summary": {
                    "monthly_income": request.monthly_income,
                },
            }

            final_state = await self.graph.ainvoke(initial_state, config=config)
            execution_time_ms = int((time.time() - start_time) * 1000)
            response_payload = final_state.get("final_response_payload", {})

            if not response_payload:
                raise HTTPException(
                    status_code=500,
                    detail="Graph execution completed but no final response payload was produced.",
                )

            audit_narrative = build_audit_narrative(final_state, response_payload)

            decision = response_payload.get("decision", "UNKNOWN")
            counter_offer_data = response_payload.get("counter_offer")

            await self.underwriting_repo.save_decision(
                application_id=request.application_id,
                decision=decision,
                final_decision=response_payload,
                aggregated_risk_score=final_state.get("aggregated_risk_score"),
                aggregated_risk_tier=final_state.get("aggregated_risk_tier"),
                counter_offer_data=counter_offer_data,
                thread_id=thread_id,
                execution_time_ms=execution_time_ms,
                parallel_tasks_executed=final_state.get("parallel_tasks_completed", []),
                node_execution_times=final_state.get("node_execution_times", {}),
                policy_version=(final_state.get("policy_metadata") or {}).get("policy_version"),
                model_version=(final_state.get("version_metadata") or {}).get("model_version"),
                prompt_version=(final_state.get("version_metadata") or {}).get("prompt_version"),
                audit_narrative=audit_narrative,
                raw_state=final_state,
            )

            await self.idempotency_repo.mark_completed(
                request.application_id,
                response_payload,
            )
            await self.failed_thread_repo.delete_failed_thread(request.application_id)
            return response_payload

        except (DuplicateRequestInProgressError, IdempotencyConflictError) as exc:
            status = "FAILURE"
            error_message = str(exc)
            raise HTTPException(status_code=409, detail=error_message) from exc
        except HTTPException as exc:
            status = "FAILURE"
            error_message = str(exc.detail)
            if started_processing:
                await self.idempotency_repo.mark_failed(
                    request.application_id,
                    error_message,
                )
            await self.failed_thread_repo.save_failure(
                application_id=request.application_id,
                thread_id=thread_id,
                error_message=error_message,
            )
            raise
        except Exception as exc:
            status = "FAILURE"
            error_message = str(exc)
            if started_processing:
                await self.idempotency_repo.mark_failed(
                    request.application_id,
                    error_message,
                )
            await self.failed_thread_repo.save_failure(
                application_id=request.application_id,
                thread_id=thread_id,
                error_message=error_message,
            )
            raise HTTPException(status_code=500, detail=error_message) from exc
        finally:
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self.service_audit_repo.save_log(
                application_id=request.application_id,
                correlation_id=correlation_id,
                agent_name="decisioning_agent",
                operation_name="underwrite",
                request_payload=request_payload,
                response_payload=response_payload,
                status=status,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
            )
