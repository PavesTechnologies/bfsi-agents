"""Core orchestration service for the cross-agent loan pipeline."""

from copy import deepcopy
import json
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx

from shared.data_mappers import (
    map_decisioning_to_disbursement,
    map_intake_to_india_kyc,
    map_intake_to_indian_underwriting,
)

HARDCODED_MONTHLY_INCOME = 75000.0
from shared.pipeline_events import PipelineEvent, PipelineStage
from src.config import AgentConfig
from src.store.pipeline_state_store import clear_state, get_state, save_state
from src.utils.offer_generator import calculate_emi, generate_counter_offer_options


ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class PipelineService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=AgentConfig.REQUEST_TIMEOUT_SECONDS)

    async def _emit_progress(
        self,
        application_id: str,
        progress_callback: Optional[ProgressCallback],
        event: PipelineEvent | str,
        stage: PipelineStage,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        is_terminal: bool = False,
    ) -> None:
        if progress_callback is None:
            return

        payload: Dict[str, Any] = {
            "application_id": application_id,
            "event": event.value if isinstance(event, PipelineEvent) else event,
            "stage": stage.value,
            "status": status,
            "message": message,
            "is_terminal": is_terminal,
        }
        if details:
            payload["details"] = details

        print(f"Emitting progress update: {json.dumps(payload, indent=2)}")

        await progress_callback(payload)

    async def execute_full_pipeline(
        self,
        application_id: str,
        raw_application: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        return await self.execute_until_decision(
            application_id=application_id,
            raw_application=raw_application,
            progress_callback=progress_callback,
        )

    async def execute_until_decision(
        self,
        application_id: str,
        raw_application: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Run India KYC → CIBIL underwriting, then pause for any required user action."""
        print(f"Triggering pipeline for application_id: {application_id}")
        print(json.dumps(raw_application, indent=2))

        applicants = raw_application.get("applicants", [])
        applicant_data = deepcopy(applicants[0] if applicants else {})

        # ── KYC Stage ──────────────────────────────────────────────────────────
        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.KYC_TRIGGERED,
            stage=PipelineStage.KYC,
            status="started",
            message="India KYC verification started",
        )

        kyc_payload = map_intake_to_india_kyc(
            application_id=application_id,
            applicant=applicant_data,
            idempotency_key=f"kyc_{application_id}",
        )
        print(json.dumps(kyc_payload, indent=2))

        try:
            kyc_response = await self.http_client.post(
                f"{AgentConfig.KYC_AGENT_URL}/kyc/india/kyc/execute",
                json=kyc_payload,
                headers={"X-Idempotency-Key": f"kyc_{application_id}"},
            )
            self._raise_for_status_with_detail(kyc_response, "India KYC execute")
            kyc_data = kyc_response.json()
        except Exception as exc:
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.KYC_FAILED,
                stage=PipelineStage.KYC,
                status="failed",
                message="India KYC verification failed",
                details={"reason": str(exc)},
                is_terminal=True,
            )
            raise

        print(json.dumps(kyc_data, indent=2))

        kyc_status = kyc_data.get("kyc_status")
        if kyc_status != "PASS":
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.KYC_FAILED,
                stage=PipelineStage.KYC,
                status="failed",
                message="India KYC verification did not pass",
                details={
                    "kyc_status": kyc_status,
                    "hard_fail_rules": kyc_data.get("hard_fail_rules", []),
                    "soft_flags": kyc_data.get("soft_flags", []),
                    "decision_explanation": kyc_data.get("decision_explanation"),
                },
                is_terminal=True,
            )
            return {
                "status": "REJECTED_AT_KYC",
                "application_id": application_id,
                "kyc_details": kyc_data,
            }

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.KYC_PASSED,
            stage=PipelineStage.KYC,
            status="completed",
            message="India KYC verification passed",
            details={
                "confidence_score": kyc_data.get("confidence_score"),
                "ckyc_id": kyc_data.get("ckyc_id"),
            },
        )

        # ── Underwriting Stage (Indian RAG) ────────────────────────────────────
        underwriting_payload = map_intake_to_indian_underwriting(
            application_id=application_id,
            applicant=applicant_data,
            requested_amount=self._extract_requested_amount(raw_application),
            requested_tenure_months=self._extract_requested_tenure(raw_application),
            monthly_income=HARDCODED_MONTHLY_INCOME,
        )
        print(json.dumps(underwriting_payload, indent=2))

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.UNDERWRITING_STARTED,
            stage=PipelineStage.DECISIONING,
            status="started",
            message="Indian credit decisioning started",
        )

        try:
            uw_response = await self.http_client.post(
                f"{AgentConfig.DECISIONING_AGENT_URL}/underwrite/indian",
                json=underwriting_payload,
                timeout=AgentConfig.UNDERWRITING_TIMEOUT_SECONDS,
            )
            self._raise_for_status_with_detail(uw_response, "Indian underwrite")
            uw_raw = uw_response.json()
            uw_data = self._normalize_underwriting_response(uw_raw)
            print("Underwriting data received:", json.dumps(uw_data, indent=2))
        except Exception as exc:
            reason = str(exc) or repr(exc) or exc.__class__.__name__
            print(f"Indian underwrite call failed: {reason}")
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event="UNDERWRITING_FAILED",
                stage=PipelineStage.DECISIONING,
                status="failed",
                message="Indian credit decisioning failed",
                details={"reason": reason, "error_type": exc.__class__.__name__},
                is_terminal=True,
            )
            raise

        decision = uw_data.get("decision")
        print(f"Underwriting decision: {decision}")

        if decision == "DECLINE":
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.APPLICATION_DECLINED,
                stage=PipelineStage.DECISIONING,
                status="completed",
                message="Credit decisioning completed: application declined",
                details={
                    "decision": decision,
                    "reason": uw_data.get("decline_reason") or uw_data.get("explanation"),
                },
                is_terminal=True,
            )
            return {
                "status": "DECLINED",
                "application_id": application_id,
                "underwriting_details": uw_data,
            }

        if decision == "APPROVE":
            save_state(
                application_id,
                {
                    "phase": "AWAITING_APPROVAL_CONFIRMATION",
                    "uw_data": deepcopy(uw_data),
                },
            )
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.APPLICATION_APPROVED,
                stage=PipelineStage.DECISIONING,
                status="completed",
                message="Credit decisioning completed: application approved",
                details={
                    "decision": decision,
                    "reason": uw_data.get("explanation") or uw_data.get("terms_summary"),
                    "approved_amount": uw_data.get("approved_amount"),
                    "approved_tenure_months": uw_data.get("approved_tenure"),
                    "interest_rate": uw_data.get("interest_rate"),
                    "monthly_emi": uw_data.get("monthly_emi"),
                    "processing_fee": uw_data.get("processing_fee"),
                    "terms_summary": uw_data.get("terms_summary"),
                },
                is_terminal=True,
            )
            return {
                "status": "AWAITING_APPROVAL_CONFIRMATION",
                "application_id": application_id,
                "approved_amount": uw_data["approved_amount"],
                "approved_tenure_months": uw_data["approved_tenure"],
                "interest_rate": uw_data["interest_rate"],
                "monthly_emi": uw_data["monthly_emi"],
                "processing_fee": uw_data.get("processing_fee", 0.0),
                "terms_summary": uw_data.get("terms_summary", ""),
                "underwriting_details": uw_data,
            }

        if decision == "COUNTER_OFFER":
            print("Generating counter offer options..........................")
            options = uw_data.get("counter_offer_data")
            uw_data["counter_offer_options"] = options.get("generated_options")
            print("Before saving state")
            save_state(
                application_id,
                {
                    "phase": "AWAITING_OFFER_SELECTION",
                    "uw_data": deepcopy(uw_data),
                    "options": deepcopy(options),
                },
            )
            print("Counter offer options generated************************")
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.COUNTER_OFFER_PENDING,
                stage=PipelineStage.DECISIONING,
                status="completed",
                message="Credit decisioning completed: counter offer generated",
                details={
                    "decision": decision,
                    "reason": uw_data.get("original_decision_explanation") or uw_data.get("explanation"),
                    "counter_offer_options": options,
                },
                is_terminal=True,
            )
            return {
                "status": "COUNTER_OFFER_PENDING",
                "application_id": application_id,
                "counter_offer_options": options,
                "underwriting_details": uw_data,
            }

        raise ValueError(f"Unsupported underwriting decision: {decision}")

    # ── HITL flow ────────────────────────────────────────────────────────────

    async def execute_until_bank_review(
        self,
        application_id: str,
        raw_application: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Run KYC → create LoanApplication in bank-admin → pause for bank review."""
        from copy import deepcopy

        applicants = raw_application.get("applicants", [])
        applicant_data = deepcopy(applicants[0] if applicants else {})

        # ── KYC ────────────────────────────────────────────────────────────
        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.KYC_TRIGGERED,
            stage=PipelineStage.KYC,
            status="started",
            message="India KYC verification started",
        )

        kyc_payload = map_intake_to_india_kyc(
            application_id=application_id,
            applicant=applicant_data,
            idempotency_key=f"kyc_{application_id}",
        )

        try:
            kyc_response = await self.http_client.post(
                f"{AgentConfig.KYC_AGENT_URL}/kyc/india/kyc/execute",
                json=kyc_payload,
                headers={"X-Idempotency-Key": f"kyc_{application_id}"},
            )
            self._raise_for_status_with_detail(kyc_response, "India KYC execute")
            kyc_data = kyc_response.json()
        except Exception as exc:
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.KYC_FAILED,
                stage=PipelineStage.KYC,
                status="failed",
                message="India KYC verification failed",
                details={"reason": str(exc)},
                is_terminal=True,
            )
            raise

        kyc_status = kyc_data.get("kyc_status")
        if kyc_status != "PASS":
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.KYC_FAILED,
                stage=PipelineStage.KYC,
                status="failed",
                message="India KYC verification did not pass",
                details={
                    "kyc_status": kyc_status,
                    "hard_fail_rules": kyc_data.get("hard_fail_rules", []),
                    "soft_flags": kyc_data.get("soft_flags", []),
                    "decision_explanation": kyc_data.get("decision_explanation"),
                },
                is_terminal=True,
            )
            return {"status": "REJECTED_AT_KYC", "application_id": application_id}

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.KYC_PASSED,
            stage=PipelineStage.KYC,
            status="completed",
            message="India KYC verification passed",
            details={
                "confidence_score": kyc_data.get("confidence_score"),
                "ckyc_id": kyc_data.get("ckyc_id"),
            },
        )

        # ── Create LoanApplication in bank-admin ────────────────────────
        name_parts = filter(None, [
            applicant_data.get("first_name", ""),
            applicant_data.get("middle_name"),
            applicant_data.get("last_name", ""),
        ])
        full_name = " ".join(name_parts).strip()

        bank_payload = {
            "external_application_id": application_id,
            "kyc_status": kyc_status,
            "kyc_result_snapshot": kyc_data,
            "applicant_snapshot": {
                "full_name": full_name,
                "pan_number": applicant_data.get("pan_number", ""),
                "aadhaar_number": applicant_data.get("aadhaar_no") or applicant_data.get("aadhaar_number", ""),
                "phone": applicant_data.get("phone_number", ""),
                "email": applicant_data.get("email", ""),
                "date_of_birth": str(applicant_data.get("date_of_birth", "")),
            },
            "loan_amount_requested": self._extract_requested_amount(raw_application),
            "loan_tenure_months": self._extract_requested_tenure(raw_application),
            "loan_purpose": raw_application.get("loan_purpose"),
        }

        try:
            bank_resp = await self.http_client.post(
                f"{AgentConfig.BANK_ADMIN_URL}/api/v1/pipeline/applications",
                json=bank_payload,
            )
            self._raise_for_status_with_detail(bank_resp, "Bank-admin create application")
        except Exception as exc:
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event="PIPELINE_FAILED",
                stage=PipelineStage.KYC,
                status="failed",
                message="Failed to register application with bank",
                details={"reason": str(exc)},
                is_terminal=True,
            )
            raise

        save_state(
            application_id,
            {
                "phase": "AWAITING_BANK_REVIEW",
                "kyc_data": kyc_data,
                "raw_application": raw_application,
            },
        )

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.AWAITING_BANK_REVIEW,
            stage=PipelineStage.DECISIONING,
            status="pending",
            message="Application submitted for bank review",
            is_terminal=False,
        )

        return {"status": "AWAITING_BANK_REVIEW", "application_id": application_id}

    async def run_decisioning(
        self,
        application_id: str,
        active_analyzers: Optional[List[str]],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Run underwriting for a HITL application. Called by /internal/run-decisioning."""
        state = get_state(application_id)
        if not state or state.get("phase") != "AWAITING_BANK_REVIEW":
            raise ValueError(f"No pending bank review for application {application_id}")

        raw_application = state["raw_application"]
        applicants = raw_application.get("applicants", [])
        applicant_data = deepcopy(applicants[0] if applicants else {})

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.BANK_DECISIONING_STARTED,
            stage=PipelineStage.DECISIONING,
            status="started",
            message="Bank triggered credit decisioning",
        )

        underwriting_payload = map_intake_to_indian_underwriting(
            application_id=application_id,
            applicant=applicant_data,
            requested_amount=self._extract_requested_amount(raw_application),
            requested_tenure_months=self._extract_requested_tenure(raw_application),
            monthly_income=HARDCODED_MONTHLY_INCOME,
        )
        if active_analyzers is not None:
            underwriting_payload["active_analyzers"] = active_analyzers

        try:
            uw_response = await self.http_client.post(
                f"{AgentConfig.DECISIONING_AGENT_URL}/underwrite/indian",
                json=underwriting_payload,
                timeout=AgentConfig.UNDERWRITING_TIMEOUT_SECONDS,
            )
            self._raise_for_status_with_detail(uw_response, "Indian underwrite")
            uw_raw = uw_response.json()
            uw_data = self._normalize_underwriting_response(uw_raw)
        except Exception as exc:
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event="UNDERWRITING_FAILED",
                stage=PipelineStage.DECISIONING,
                status="failed",
                message="Credit decisioning failed",
                details={"reason": str(exc)},
                is_terminal=True,
            )
            raise

        # Build decisioning result patch for bank-admin
        co_raw = uw_raw.get("counter_offer") or {}
        counter_offer_options = None
        if co_raw:
            counter_offer_options = [
                {
                    "option_id": o.get("option_id"),
                    "description": o.get("description"),
                    "proposed_amount": o.get("proposed_amount"),
                    "proposed_tenure_months": o.get("proposed_tenure_months"),
                    "proposed_interest_rate": o.get("proposed_interest_rate"),
                    "disbursement_amount": o.get("disbursement_amount"),
                    "monthly_payment_emi": o.get("monthly_payment_emi"),
                    "total_repayment": o.get("total_repayment"),
                }
                for o in co_raw.get("generated_options", [])
            ]

        try:
            patch_resp = await self.http_client.patch(
                f"{AgentConfig.BANK_ADMIN_URL}/api/v1/pipeline/applications/{application_id}/decisioning-result",
                json={
                    "llm_decision": uw_data.get("decision"),
                    "llm_risk_tier": uw_raw.get("risk_tier"),
                    "llm_risk_score": uw_raw.get("risk_score"),
                    "llm_approved_amount": uw_data.get("approved_amount"),
                    "llm_interest_rate": uw_data.get("interest_rate"),
                    "llm_tenure_months": uw_data.get("approved_tenure") or uw_data.get("approved_tenure_months"),
                    "llm_counter_offer_options": counter_offer_options,
                    "decisioning_result_snapshot": uw_raw,
                },
            )
            self._raise_for_status_with_detail(patch_resp, "Bank-admin patch decisioning-result")
        except Exception as exc:
            raise RuntimeError(f"Failed to save decisioning result to bank-admin: {exc}") from exc

        save_state(
            application_id,
            {
                "phase": "AWAITING_BANK_DECISION",
                "kyc_data": state.get("kyc_data"),
                "raw_application": raw_application,
                "uw_data": uw_data,
                "uw_raw": uw_raw,
                "counter_offer_options": counter_offer_options,
            },
        )

    async def notify_applicant_of_bank_decision(
        self,
        application_id: str,
        final_decision: str,
        approved_amount: Optional[float],
        interest_rate: Optional[float],
        tenure_months: Optional[int],
        monthly_emi: Optional[float],
        counter_offer_options: Optional[List[Any]],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Push bank decision to applicant's SSE stream. Called by /internal/notify-bank-decision."""
        state = get_state(application_id)
        if not state:
            raise ValueError(f"No pipeline state for application {application_id}")

        if final_decision == "DECLINE":
            save_state(application_id, {**state, "phase": "BANK_DECLINED"})
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.APPLICATION_DECLINED,
                stage=PipelineStage.DECISIONING,
                status="completed",
                message="Bank declined the loan application",
                details={"decision": "DECLINE"},
                is_terminal=True,
            )
            return

        save_state(
            application_id,
            {
                **state,
                "phase": "AWAITING_APPLICANT_RESPONSE",
                "bank_decision": final_decision,
                "approved_amount": approved_amount,
                "interest_rate": interest_rate,
                "tenure_months": tenure_months,
                "monthly_emi": monthly_emi,
                "counter_offer_options": counter_offer_options,
            },
        )

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.AWAITING_APPLICANT_RESPONSE,
            stage=PipelineStage.DECISIONING,
            status="completed",
            message="Bank decision ready — awaiting applicant response",
            details={
                "final_decision": final_decision,
                "approved_amount": approved_amount,
                "interest_rate": interest_rate,
                "tenure_months": tenure_months,
                "monthly_emi": monthly_emi,
                "counter_offer_options": counter_offer_options,
            },
            is_terminal=False,
        )

    async def applicant_accept(
        self,
        application_id: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Applicant accepts the bank offer. Sets state to AWAITING_SIGNATURE."""
        state = get_state(application_id)
        if not state or state.get("phase") != "AWAITING_APPLICANT_RESPONSE":
            raise ValueError(f"No pending offer for application {application_id}")

        try:
            resp = await self.http_client.patch(
                f"{AgentConfig.BANK_ADMIN_URL}/api/v1/pipeline/applications/by-external/{application_id}/awaiting-signature",
            )
            self._raise_for_status_with_detail(resp, "Bank-admin set awaiting-signature")
        except Exception as exc:
            raise RuntimeError(f"Failed to update bank-admin awaiting-signature: {exc}") from exc

        save_state(application_id, {**state, "phase": "AWAITING_SIGNATURE"})

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.APPLICANT_ACCEPTED,
            stage=PipelineStage.DECISIONING,
            status="completed",
            message="Applicant accepted the offer — please sign the loan agreement",
            is_terminal=False,
        )

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.AWAITING_SIGNATURE,
            stage=PipelineStage.DISBURSEMENT,
            status="pending",
            message="Awaiting digital signature on loan agreement",
            is_terminal=False,
        )

    async def applicant_decline(
        self,
        application_id: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Applicant declines the bank offer."""
        try:
            resp = await self.http_client.patch(
                f"{AgentConfig.BANK_ADMIN_URL}/api/v1/pipeline/applications/by-external/{application_id}/cancelled",
            )
            self._raise_for_status_with_detail(resp, "Bank-admin set cancelled")
        except Exception as exc:
            raise RuntimeError(f"Failed to update bank-admin cancelled: {exc}") from exc

        clear_state(application_id)

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.APPLICATION_DECLINED_BY_APPLICANT,
            stage=PipelineStage.DECISIONING,
            status="completed",
            message="Applicant declined the loan offer",
            is_terminal=True,
        )

    async def submit_signature(
        self,
        application_id: str,
        full_name: str,
        agreed: bool,
        ip: Optional[str],
        user_agent: Optional[str],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Save signature, then trigger disbursement."""
        state = get_state(application_id)
        if not state or state.get("phase") != "AWAITING_SIGNATURE":
            raise ValueError(f"No pending signature for application {application_id}")

        if not agreed:
            raise ValueError("Signature must include agreement (agreed=true)")

        try:
            sig_resp = await self.http_client.patch(
                f"{AgentConfig.BANK_ADMIN_URL}/api/v1/pipeline/applications/by-external/{application_id}/signature",
                json={"full_name": full_name, "agreed": agreed, "ip": ip, "user_agent": user_agent},
            )
            self._raise_for_status_with_detail(sig_resp, "Bank-admin save signature")
        except Exception as exc:
            raise RuntimeError(f"Failed to save signature: {exc}") from exc

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.SIGNATURE_RECEIVED,
            stage=PipelineStage.DISBURSEMENT,
            status="completed",
            message="Digital signature received — proceeding to disbursement",
        )

        save_state(application_id, {**state, "phase": "SIGNATURE_COMPLETE"})

        # Build disbursement payload from bank decision state
        uw_data = state.get("uw_data") or {}
        uw_data["approved_amount"] = state.get("approved_amount") or uw_data.get("approved_amount")
        uw_data["interest_rate"] = state.get("interest_rate") or uw_data.get("interest_rate")
        uw_data["approved_tenure_months"] = state.get("tenure_months") or uw_data.get("approved_tenure") or uw_data.get("approved_tenure_months")
        uw_data["monthly_emi"] = state.get("monthly_emi") or uw_data.get("monthly_emi")

        disburse_payload = map_decisioning_to_disbursement(decisioning_response={**uw_data, "application_id": application_id})

        disburse_data = await self._disburse(
            application_id=application_id,
            disburse_payload=disburse_payload,
            progress_callback=progress_callback,
        )

        # Save disbursement result to bank-admin
        try:
            disb_resp = await self.http_client.patch(
                f"{AgentConfig.BANK_ADMIN_URL}/api/v1/pipeline/applications/by-external/{application_id}/disbursement",
                json={
                    "transaction_id": disburse_data.get("transaction_id") or str(uuid.uuid4()),
                    "disbursed_amount": float(disburse_data.get("disbursement_amount") or disburse_data.get("approved_amount", 0)),
                    "disbursement_receipt_snapshot": disburse_data,
                },
            )
            self._raise_for_status_with_detail(disb_resp, "Bank-admin save disbursement")
        except Exception as exc:
            raise RuntimeError(f"Failed to save disbursement: {exc}") from exc

        clear_state(application_id)
        return disburse_data

    async def resume_after_counter_offer_selection(
        self,
        application_id: str,
        selected_offer_id: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Resume the pipeline after the user picks a counter offer."""
        state = get_state(application_id)
        if not state or state.get("phase") != "AWAITING_OFFER_SELECTION":
            raise ValueError(
                f"No pending counter offer selection for application {application_id}"
            )

        options = state.get("options", [])
        selected = next(
            (option for option in options if option.get("offer_id") == selected_offer_id),
            None,
        )
        if not selected:
            raise ValueError(f"Invalid offer_id: {selected_offer_id}")

        uw_data = deepcopy(state["uw_data"])
        uw_data["approved_amount"] = selected["principal_amount"]
        uw_data["approved_tenure_months"] = selected["tenure_months"]
        uw_data["interest_rate"] = selected["interest_rate"]
        uw_data["monthly_emi"] = selected["monthly_emi"]
        uw_data["processing_fee"] = round(
            float(uw_data.get("processing_fee", 0.0)),
            2,
        )
        uw_data["disbursement_amount"] = round(
            selected["principal_amount"] - uw_data["processing_fee"],
            2,
        )

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.COUNTER_OFFER_ACCEPTED,
            stage=PipelineStage.DECISIONING,
            status="completed",
            message="Counter offer selected",
            details={"selected_offer_id": selected_offer_id},
        )

        disburse_payload = map_decisioning_to_disbursement(
            decisioning_response=uw_data,
            selected_option_id=selected_offer_id,
        )
        disburse_data = await self._disburse(
            application_id=application_id,
            disburse_payload=disburse_payload,
            progress_callback=progress_callback,
        )
        clear_state(application_id)

        return {
            "status": "DISBURSED",
            "application_id": application_id,
            "disbursement_receipt": disburse_data,
        }

    async def resume_after_approval_confirmation(
        self,
        application_id: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Resume the pipeline after the user accepts approved terms."""
        state = get_state(application_id)
        if not state or state.get("phase") != "AWAITING_APPROVAL_CONFIRMATION":
            raise ValueError(
                f"No pending approval confirmation for application {application_id}"
            )

        uw_data = deepcopy(state["uw_data"])
        disburse_payload = map_decisioning_to_disbursement(decisioning_response=uw_data)
        disburse_data = await self._disburse(
            application_id=application_id,
            disburse_payload=disburse_payload,
            progress_callback=progress_callback,
        )
        clear_state(application_id)

        return {
            "status": "DISBURSED",
            "application_id": application_id,
            "disbursement_receipt": disburse_data,
        }

    def cancel_pending_application(self, application_id: str) -> Dict[str, Any]:
        """Cancel any paused pipeline state for an application."""
        clear_state(application_id)
        return {
            "status": "CANCELLED_BY_USER",
            "application_id": application_id,
        }

    async def _disburse(
        self,
        application_id: str,
        disburse_payload: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.DISBURSEMENT_STARTED,
            stage=PipelineStage.DISBURSEMENT,
            status="started",
            message="Disbursement started",
        )

        try:
            disburse_response = await self.http_client.post(
                f"{AgentConfig.DISBURSEMENT_AGENT_URL}/disburse",
                json=disburse_payload,
            )
            self._raise_for_status_with_detail(disburse_response, "Disbursement disburse")
            disburse_data = disburse_response.json()
        except Exception as exc:
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.DISBURSEMENT_FAILED,
                stage=PipelineStage.DISBURSEMENT,
                status="failed",
                message="Disbursement failed",
                details={"reason": str(exc)},
                is_terminal=True,
            )
            raise

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.FUNDS_DISBURSED,
            stage=PipelineStage.DISBURSEMENT,
            status="completed",
            message="Disbursement completed",
            is_terminal=True,
        )
        return disburse_data

    @staticmethod
    def _raise_for_status_with_detail(response: httpx.Response, step: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = PipelineService._extract_error_detail(response)
            raise RuntimeError(
                f"{step} failed with status {response.status_code}: {detail}"
            ) from exc

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text or response.reason_phrase

        if isinstance(payload, dict):
            return str(payload.get("detail") or payload)
        return str(payload)

    @staticmethod
    def _extract_requested_amount(raw_application: Dict[str, Any]) -> float:
        return float(raw_application.get("requested_amount") or 100000.0)

    @staticmethod
    def _extract_requested_tenure(raw_application: Dict[str, Any]) -> int:
        return int(raw_application.get("requested_term_months") or 36)

    def _normalize_underwriting_response(self, uw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize underwriting output into a single orchestrator-friendly shape."""
        normalized = deepcopy(uw_data)

        loan_details = normalized.get("loan_details") or {}
        if loan_details:
            normalized["approved_amount"] = loan_details.get("approved_amount")
            normalized["approved_tenure_months"] = loan_details.get(
                "approved_tenure_months"
            )
            normalized["interest_rate"] = loan_details.get("interest_rate")
            normalized["disbursement_amount"] = loan_details.get("disbursement_amount")
            if not normalized.get("terms_summary"):
                normalized["terms_summary"] = loan_details.get("explanation", "")

        counter_offer = normalized.get("counter_offer") or {}
        if counter_offer and not normalized.get("counter_offer_options"):
            normalized["counter_offer_options"] = [
                {
                    "offer_id": option.get("option_id"),
                    "principal_amount": option.get("proposed_amount"),
                    "tenure_months": option.get("proposed_tenure_months"),
                    "interest_rate": option.get("proposed_interest_rate"),
                    "monthly_emi": option.get("monthly_payment_emi"),
                    "label": option.get("description", "Offer Option"),
                    "disbursement_amount": option.get("disbursement_amount"),
                    "total_repayment": option.get("total_repayment"),
                }
                for option in counter_offer.get("generated_options", [])
            ]

        if normalized.get("approved_amount") and normalized.get("approved_tenure_months"):
            normalized["monthly_emi"] = normalized.get("monthly_emi") or calculate_emi(
                float(normalized["approved_amount"]),
                float(normalized["interest_rate"]),
                int(normalized["approved_tenure_months"]),
            )
            if normalized.get("disbursement_amount") is None:
                normalized["disbursement_amount"] = normalized["approved_amount"]
            normalized["processing_fee"] = round(
                float(normalized["approved_amount"])
                - float(normalized["disbursement_amount"]),
                2,
            )
            if not normalized.get("terms_summary"):
                normalized["terms_summary"] = (
                    f"Loan of ₹{float(normalized['approved_amount']):,.2f} at "
                    f"{float(normalized['interest_rate']):.2f}% for "
                    f"{int(normalized['approved_tenure_months'])} months. "
                    f"EMI: ₹{float(normalized['monthly_emi']):,.2f}/month."
                )

        return normalized

    async def close(self):
        await self.http_client.aclose()
