# src/services/post_kyc_cibil_service.py
"""
Post-KYC Credit Decisioning Service  (Indian Bureau — CIBIL)

Workflow
────────
  [KYC Agent hands off verified PAN]
          │
          ▼
  1. MockCIBILAdapter.get_credit_report(pan)
          │  CIBILResponse
          ▼
  2. _cibil_to_decisioning_dict()          ← maps CIBIL → Experian-compat schema
          │  raw_experian_data dict
          ▼
  3. LangGraph  build_underwriting_graph()
       pi_deletion_node
          ├── credit_score_node      (LLM 1 — CIBIL score band)
          ├── public_record_node     (LLM 2 — suit / wilful-default / DRT)
          ├── credit_utilization     (LLM 3 — revolving utilization)
          ├── debt_exposure          (LLM 4 — open-account outstanding)
          ├── payment_behavior       (LLM 5 — DPD / charge-off history)
          ├── inquiry                (LLM 6 — enquiry velocity)
          └── income_analysis        (LLM 7 — DTI / affordability)
               └── risk_aggregator_node
                    └── decision_llm_node
                         └── counter_offer | final_response
          │
          ▼
  4. Persist decision → underwriting_decisions table
          │
          ▼
  5. Return final_decision payload
"""

import sys
import os
import time
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# ── CIBIL adapter (kyc_agent sibling package) ────────────────────────────────
# In production the CIBIL report arrives as a JSON payload from the KYC agent
# API.  For dev/test we import the mock adapter directly.
_KYC_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "kyc_agent", "src"
)
sys.path.insert(0, os.path.abspath(_KYC_SRC))
from adapters.mock_adapters.mock_cibil_adapter import (  # type: ignore
    MockCIBILAdapter,
    CIBILResponse,
)

from src.workflows.decision_flow import build_underwriting_graph
from src.repositories.langgraph_failed_th_repository import (
    DecisioningFailedThreadRepository,
)
from src.repositories.underwriting_repository import UnderwritingRepository


class PostKYCCIBILService:
    """
    Orchestrates the post-KYC credit-decisioning pipeline for Indian applicants.

    Entry  : verified PAN from the KYC agent
    Exit   : final underwriting decision dict
             (decision, approved_amount, interest_rate, explanation, …)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.failed_thread_repo = DecisioningFailedThreadRepository(db)
        self.underwriting_repo = UnderwritingRepository(db)
        self.graph = build_underwriting_graph()
        self.cibil_adapter = MockCIBILAdapter()

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC
    # ─────────────────────────────────────────────────────────────────────────

    async def execute(
        self,
        *,
        pan: str,
        full_name: str,
        application_id: str,
        requested_amount: float,
        requested_tenure_months: int,
        monthly_income: float,
    ) -> dict[str, Any]:
        """
        Run the full post-KYC → credit decision pipeline.

        Parameters
        ──────────
        pan                      PAN number verified by KYC agent
        full_name                Applicant full name (for CIBIL mock identity)
        application_id           Unique loan application ID
        requested_amount         Requested loan amount (INR)
        requested_tenure_months  Requested tenure in months
        monthly_income           Gross monthly income from bank statement (INR)

        Returns
        ───────
        final_decision dict with keys: decision, approved_amount,
        approved_tenure, interest_rate, disbursement_amount, explanation,
        reasoning_steps, [counter_offer_data]
        """

        # ── Step 1: Fetch CIBIL report ────────────────────────────────────
        cibil_report: CIBILResponse = await self.cibil_adapter.get_credit_report(
            {"pan": pan, "full_name": full_name}
        )

        # ── Step 2: Map to decisioning-compatible format ──────────────────
        #   The 7 parallel nodes all read from `pi_masked_experian_data`.
        #   We populate `raw_experian_data` with CIBIL-mapped keys so the
        #   existing pi_deletion_node + all 7 LLM nodes require zero changes.
        decisioning_dict = self._cibil_to_decisioning_dict(cibil_report)

        # ── Step 3: Resolve thread id (idempotency / retry) ──────────────
        failed = await self.failed_thread_repo.get_failed_thread(application_id)
        thread_id = (
            failed.thread_id if failed else f"cibil_uw_{application_id}"
        )
        config = {"configurable": {"thread_id": thread_id}}

        # ── Step 4: Build initial LangGraph state ─────────────────────────
        initial_state: dict[str, Any] = {
            "application_id": application_id,
            "correlation_id": str(uuid.uuid4()),
            # Passed as raw_experian_data so pi_deletion_node strips PII
            # and all 7 downstream nodes read from pi_masked_experian_data.
            "raw_experian_data": decisioning_dict,
            "user_request": {
                "amount": requested_amount,
                "tenure": requested_tenure_months,
            },
            "bank_statement_summary": {
                "monthly_income": monthly_income,
            },
        }

        # ── Step 5: Invoke LangGraph (7 parallel LLM nodes) ──────────────
        try:
            start_time = time.time()
            final_state = await self.graph.ainvoke(initial_state, config=config)
            execution_time_ms = int((time.time() - start_time) * 1000)

            response_payload: dict[str, Any] = final_state.get("final_decision") or {}
            if not response_payload:
                raise HTTPException(
                    status_code=500,
                    detail="Underwriting graph completed with no final_decision in state.",
                )

            decision = response_payload.get("decision", "UNKNOWN")
            counter_offer_data = None
            if decision == "COUNTER_OFFER":
                counter_offer_data = final_state.get("counter_offer_data", {})
                response_payload["counter_offer_data"] = counter_offer_data
            else:
                # max_approved_amount is meaningful only in the COUNTER_OFFER
                # branch — strip it elsewhere so the response isn't misread.
                response_payload.pop("max_approved_amount", None)

            # ── Step 6: Persist decision with full audit trail ────────────
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
                error_message="HTTPException during CIBIL underwriting",
            )
            raise
        except Exception as exc:
            await self.failed_thread_repo.save_failure(
                application_id=application_id,
                thread_id=thread_id,
                error_message=str(exc),
            )
            raise HTTPException(status_code=500, detail=str(exc))

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE
    # ─────────────────────────────────────────────────────────────────────────

    def _cibil_to_decisioning_dict(self, report: CIBILResponse) -> dict[str, Any]:
        """
        Translate CIBILResponse into the Experian-compatible dict schema
        expected by all 7 decisioning nodes.

        Node → field consumed
        ─────────────────────────────────────────────────────────────────────
        credit_score_node    → riskModel[0].score
        public_record_node   → publicRecord list
        utilization_node     → tradeline (revolvingOrInstallment == "R")
        exposure_node        → tradeline (openOrClosed == "O")
        behavior_node        → tradeline (delinquencies30Days, dpdHistory)
        inquiry_node         → inquiry list
        income_node          → tradeline (monthlyPaymentAmount of open trades)
                             → bank_statement_summary.monthly_income  [in state]
        """
        return {
            # ── Node 1: credit_score ──────────────────────────────────────
            "riskModel": [rm.model_dump() for rm in report.riskModel],

            # ── Nodes 3-5 & 7: utilization / exposure / behavior / income ─
            "tradeline": [t.model_dump() for t in report.tradeline],

            # ── Node 6: inquiry ───────────────────────────────────────────
            "inquiry": [i.model_dump() for i in report.inquiry],

            # ── Node 2: public_record ─────────────────────────────────────
            "publicRecord": [p.model_dump() for p in report.publicRecord],

            # ── Utilization summary fallback ──────────────────────────────
            "summaries": report.summaries,

            # ── Identity block (pi_deletion_node strips name / address) ───
            "consumerIdentity": report.consumerIdentity.model_dump(),
            "addressInformation": [a.model_dump() for a in report.addressInformation],

            # ── CIBIL-specific risk flags (available to aggregator / LLM) ─
            "wilfulDefaulterFlag": report.wilfulDefaulterFlag,
            "suitFiledFlag": report.suitFiledFlag,
            "writtenOffFlag": report.writtenOffFlag,
            "ntcFlag": report.ntcFlag,
            "reportId": report.reportId,
            "reportDate": report.reportDate,
        }
