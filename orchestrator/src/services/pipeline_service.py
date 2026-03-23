"""Core orchestration service for the cross-agent loan pipeline."""

from copy import deepcopy
import json
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx

from shared.data_mappers import (
    map_decisioning_to_disbursement,
    map_intake_to_kyc,
    map_to_underwriting,
)
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
        """
        Execute the pipeline until a terminal state or explicit user action is required.

        This keeps the async progress/SSE flow from the rate-limiting branch while
        preserving the approval and counter-offer pause points from the
        accept-counter-offer branch.
        """
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
        """Run KYC and underwriting, then pause for any required user action."""
        print(f"Triggering pipeline for application_id: {application_id}")
        print(json.dumps(raw_application, indent=2))

        applicants = raw_application.get("applicants", [])
        applicant_data = deepcopy(applicants[0] if applicants else {})
        raw_ssn = applicant_data.get("ssn_no", "")
        applicant_data["ssn"] = raw_ssn.replace("-", "")

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.KYC_TRIGGERED,
            stage=PipelineStage.KYC,
            status="started",
            message="KYC verification started",
        )

        kyc_payload = map_intake_to_kyc(
            application_id=application_id,
            applicant=applicant_data,
            idempotency_key=f"kyc_{application_id}",
        )
        print(json.dumps(kyc_payload, indent=2))

        try:
            kyc_response = await self.http_client.post(
                f"{AgentConfig.KYC_AGENT_URL}/verify",
                json=kyc_payload,
            )
            self._raise_for_status_with_detail(kyc_response, "KYC verify")
            kyc_data = kyc_response.json()
        except Exception as exc:
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.KYC_FAILED,
                stage=PipelineStage.KYC,
                status="failed",
                message="KYC verification failed",
                details={"reason": str(exc)},
                is_terminal=True,
            )
            raise

        print(json.dumps(kyc_data, indent=2))

        if kyc_data.get("status") != "PASS":
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.KYC_FAILED,
                stage=PipelineStage.KYC,
                status="failed",
                message="KYC verification failed",
                details={"kyc_status": kyc_data.get("status")},
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
            message="KYC verification completed",
        )

        experian_mock = kyc_data.get("raw_experian_data", {})
        underwriting_payload = map_to_underwriting(
            application_id=application_id,
            raw_experian_data=experian_mock,
            requested_amount=self._extract_requested_amount(raw_application),
            requested_tenure_months=self._extract_requested_tenure(raw_application),
            incomes=applicant_data.get("incomes", []),
        )
        print(json.dumps(underwriting_payload, indent=2))

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.UNDERWRITING_STARTED,
            stage=PipelineStage.DECISIONING,
            status="started",
            message="Underwriting started",
        )

        try:
            uw_response = await self.http_client.post(
                f"{AgentConfig.DECISIONING_AGENT_URL}/underwrite",
                json=underwriting_payload,
            )
            self._raise_for_status_with_detail(uw_response, "Decisioning underwrite")
            uw_raw = uw_response.json()
            uw_data = self._normalize_underwriting_response(uw_raw)
            print("Underwriting data received:", json.dumps(uw_data, indent=2))
        except Exception as exc:
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event="UNDERWRITING_FAILED",
                stage=PipelineStage.DECISIONING,
                status="failed",
                message="Underwriting failed",
                details={"reason": str(exc)},
                is_terminal=True,
            )
            raise

        decision = uw_data.get("decision")

        if decision == "DECLINE":
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.APPLICATION_DECLINED,
                stage=PipelineStage.DECISIONING,
                status="completed",
                message="Underwriting completed: application declined",
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
                message="Underwriting completed: application approved",
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
            options = uw_data.get("counter_offer_options") or generate_counter_offer_options(
                uw_data
            )
            uw_data["counter_offer_options"] = options
            save_state(
                application_id,
                {
                    "phase": "AWAITING_OFFER_SELECTION",
                    "uw_data": deepcopy(uw_data),
                    "options": deepcopy(options),
                },
            )
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.COUNTER_OFFER_PENDING,
                stage=PipelineStage.DECISIONING,
                status="completed",
                message="Underwriting completed: counter offer generated",
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
                    f"Loan of ${float(normalized['approved_amount']):,.2f} at "
                    f"{float(normalized['interest_rate']):.2f}% for "
                    f"{int(normalized['approved_tenure_months'])} months. "
                    f"EMI: ${float(normalized['monthly_emi']):,.2f}/month."
                )

        return normalized

    async def close(self):
        await self.http_client.aclose()
