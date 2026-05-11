"""
Indian (RAG-augmented) post-KYC credit decisioning service.

Mirrors PostKYCCIBILService but invokes the Indian graph
(`build_indian_underwriting_graph`) which inserts a `rag_retrieval`
step between PII deletion and the parallel analyzers, and then weaves
the retrieved RBI / bank-policy context into every analyzer prompt.

Default loan-request values are used when the caller omits them so the
existing decision / counter-offer LLM parsers stay happy.
"""

import os
import sys
import time
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Reach into the kyc_agent sibling package for the mock CIBIL adapter,
# matching the import gymnastics in post_kyc_cibil_service.py.
_KYC_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "kyc_agent", "src",
)
sys.path.insert(0, os.path.abspath(_KYC_SRC))
from adapters.mock_adapters.mock_cibil_adapter import (  # type: ignore  # noqa: E402
    CIBILResponse,
    MockCIBILAdapter,
)

from src.repositories.langgraph_failed_th_repository import (
    DecisioningFailedThreadRepository,
)
from src.repositories.underwriting_repository import UnderwritingRepository
from src.services.post_kyc_cibil_service import PostKYCCIBILService
from src.workflows.indian_decision_flow import indian_workflow_session


# Sensible retail-loan defaults — used when the request omits loan_request
# or monthly_income. Centralized here so they can be tuned in one place.
DEFAULT_LOAN_AMOUNT_INR = 500_000.0
DEFAULT_LOAN_TENURE_MONTHS = 36
DEFAULT_MONTHLY_INCOME_INR = 50_000.0


def _build_rag_response(final_state: dict[str, Any]) -> dict[str, Any]:
    """
    Compose the rag_response block for the API output. Includes:
      - pool_size: total chunks pulled from Qdrant
      - collections: which Qdrant collections contributed
      - source_documents: deduped list of source PDFs/DOCXs
      - per_node_context: the formatted re-ranked excerpt each analyzer saw
      - pool: trimmed metadata for every chunk (no embedding vectors)
    """
    pool = final_state.get("rag_pool") or []
    contexts = final_state.get("rag_context_per_node") or {}

    collections = sorted({c.get("source_collection") or "" for c in pool})
    documents = sorted({
        c.get("source_document") or "" for c in pool if c.get("source_document")
    })

    pool_preview = [
        {
            "id": c.get("id"),
            "source_collection": c.get("source_collection"),
            "source_document": c.get("source_document"),
            "section_number": c.get("section_number"),
            "section_title": c.get("section_title"),
            "breadcrumb": c.get("breadcrumb"),
            "page_numbers": c.get("page_numbers"),
            "score": c.get("score"),
        }
        for c in pool
    ]

    return {
        "pool_size": len(pool),
        "collections": [c for c in collections if c],
        "source_documents": documents,
        "per_node_context": contexts,
        "pool": pool_preview,
    }


class IndianUnderwritingService:
    """
    Run the RAG-augmented Indian decisioning pipeline.

    Entry  : Indian request payload (applicant_data + optional loan_request)
    Exit   : final underwriting decision dict — same shape as the existing
             /underwrite/cibil endpoint
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.failed_thread_repo = DecisioningFailedThreadRepository(db)
        self.underwriting_repo = UnderwritingRepository(db)
        # Graph is built per-request via `indian_workflow_session()` so the
        # checkpoint pool isn't kept open between calls.
        self.cibil_adapter = MockCIBILAdapter()

        # Reuse the CIBIL→Experian mapper from PostKYCCIBILService rather
        # than duplicating it here — same translation, same node contracts.
        self._cibil_to_decisioning_dict = (
            PostKYCCIBILService._cibil_to_decisioning_dict.__get__(self)  # type: ignore[attr-defined]
        )

    async def execute(
        self,
        *,
        application_id: str,
        pan: str,
        full_name: str,
        requested_amount: float | None,
        requested_tenure_months: int | None,
        monthly_income: float | None,
        active_analyzers: list[str] | None = None,
    ) -> dict[str, Any]:
        # Fall back to defaults when the optional blocks are absent.
        amount = requested_amount if requested_amount is not None else DEFAULT_LOAN_AMOUNT_INR
        tenure = (
            requested_tenure_months
            if requested_tenure_months is not None
            else DEFAULT_LOAN_TENURE_MONTHS
        )
        income = monthly_income if monthly_income is not None else DEFAULT_MONTHLY_INCOME_INR

        # ── 1. Pull CIBIL report ─────────────────────────────────────────
        cibil_report: CIBILResponse = await self.cibil_adapter.get_credit_report(
            {"pan": pan, "full_name": full_name}
        )

        # ── 2. CIBIL → Experian-shaped dict so existing nodes work ───────
        decisioning_dict = self._cibil_to_decisioning_dict(cibil_report)

        # ── 3. Idempotent thread id ──────────────────────────────────────
        failed = await self.failed_thread_repo.get_failed_thread(application_id)
        thread_id = failed.thread_id if failed else f"indian_uw_{application_id}"
        config = {"configurable": {"thread_id": thread_id}}

        # ── 4. Build initial graph state ─────────────────────────────────
        initial_state: dict[str, Any] = {
            "application_id": application_id,
            "correlation_id": str(uuid.uuid4()),
            "raw_experian_data": decisioning_dict,
            "user_request": {"amount": amount, "tenure": tenure},
            "bank_statement_summary": {"monthly_income": income},
            "active_analyzers": active_analyzers,
        }

        # ── 5. Invoke RAG-augmented graph ────────────────────────────────
        try:
            start = time.time()
            async with indian_workflow_session() as workflow:
                final_state = await workflow.ainvoke(initial_state, config=config)
            execution_time_ms = int((time.time() - start) * 1000)

            response_payload: dict[str, Any] = final_state.get("final_decision") or {}
            if not response_payload:
                raise HTTPException(
                    status_code=500,
                    detail="Indian underwriting graph completed with no final_decision in state.",
                )

            decision = response_payload.get("decision", "UNKNOWN")
            counter_offer_data = None
            if decision == "COUNTER_OFFER":
                counter_offer_data = final_state.get("counter_offer_data", {})
                response_payload["counter_offer_data"] = counter_offer_data
            else:
                # max_approved_amount is only meaningful as a "you qualify for up to X"
                # signal in the COUNTER_OFFER branch. Strip it from APPROVE / DECLINE
                # responses so callers don't misread it as the granted amount.
                response_payload.pop("max_approved_amount", None)

            # Surface aggregator outputs at the response top-level so the
            # orchestrator can patch llm_risk_tier / llm_risk_score on bank-admin.
            response_payload["risk_tier"] = final_state.get("aggregated_risk_tier")
            response_payload["risk_score"] = final_state.get("aggregated_risk_score")

            # Surface what RAG actually retrieved + which chunks each
            # analyzer consumed. Indian endpoint only.
            response_payload["rag_response"] = _build_rag_response(final_state)

            # ── 6. Persist with audit trail ──────────────────────────────
            await self.underwriting_repo.save_decision(
                application_id=application_id,
                decision=decision,
                final_decision=response_payload,
                aggregated_risk_score=final_state.get("aggregated_risk_score"),
                aggregated_risk_tier=final_state.get("aggregated_risk_tier"),
                counter_offer_data=counter_offer_data,
                thread_id=thread_id,
                execution_time_ms=execution_time_ms,
                parallel_tasks_executed=final_state.get("parallel_tasks_completed", []),
                node_execution_times=final_state.get("node_execution_times", {}),
                raw_state=final_state,
            )

            await self.failed_thread_repo.delete_failed_thread(application_id)
            return response_payload

        except HTTPException:
            await self.failed_thread_repo.save_failure(
                application_id=application_id,
                thread_id=thread_id,
                error_message="HTTPException during Indian underwriting",
            )
            raise
        except Exception as exc:  # noqa: BLE001
            await self.failed_thread_repo.save_failure(
                application_id=application_id,
                thread_id=thread_id,
                error_message=str(exc),
            )
            raise HTTPException(status_code=500, detail=str(exc))
