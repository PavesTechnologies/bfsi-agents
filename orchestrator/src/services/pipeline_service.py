"""
Core Pipeline Service for Orchestration

Chains the APIs of Intake, KYC, Decisioning, and Disbursement agents.
"""

import httpx
import re
from typing import Dict, Any, Awaitable, Callable, Optional
from src.config import AgentConfig
from shared.data_mappers import (
    map_intake_to_kyc,
    map_to_underwriting,
    map_decisioning_to_disbursement
)
from shared.pipeline_events import PipelineEvent, PipelineStage
import json


class PipelineService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=AgentConfig.REQUEST_TIMEOUT_SECONDS)

    async def _emit_progress(
        self,
        application_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]],
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

        await progress_callback(payload)

    async def execute_full_pipeline(
        self,
        application_id: str,
        raw_application: Dict[str, Any],
        progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the remaining loan application flow starting with KYC.
        Intake processing and document upload are assumed complete.
        """
        print(f"Triggering pipeline for application_id: {application_id}")
        print(json.dumps(raw_application, indent=2))
        
        # Extract applicant data from the raw application for subsequent mappers
        applicants = raw_application.get("applicants", [])
        applicant_data = applicants[0] if applicants else {}
        # Use regex to keep ONLY digits
        raw_ssn = applicant_data.get('ssn_no', '')

        # print(raw_ssn,"raw_ssn")
        clean_ssn = raw_ssn.replace("-", "")
        # print(clean_ssn,"clean_ssn")
        # 2. Ensure the mapper gets the clean version
        # We explicitly update the dictionary that is passed to the mapper
        applicant_data['ssn'] = clean_ssn

        # print(applicant_data,"applicant_data")

        # 2. KYC Phase
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
            idempotency_key=f"kyc_{application_id}"
        )

        
        print((json.dumps(kyc_payload, indent=2)))

        try:
            kyc_response = await self.http_client.post(
                f"{AgentConfig.KYC_AGENT_URL}/verify",
                json=kyc_payload
            )
            kyc_response.raise_for_status()
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
                "kyc_details": kyc_data
            }

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.KYC_PASSED,
            stage=PipelineStage.KYC,
            status="completed",
            message="KYC verification completed",
        )

        # 2. Decisioning Phase (Underwriting)
        # Mock Experian data for now as defined in the plan
        experian_mock = kyc_data.get("raw_experian_data", {})
        
        underwriting_payload = map_to_underwriting(
            application_id=application_id,
            raw_experian_data=experian_mock,
            requested_amount=100000.0, # Mock from intake since it's not in applicant_data
            requested_tenure_months=36,
            incomes=applicant_data.get("incomes", [])
        )

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
                json=underwriting_payload
            )
            uw_response.raise_for_status()
            uw_data = uw_response.json()
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
                details={"decision": decision},
                is_terminal=True,
            )
            return {
                "status": "DECLINED",
                "application_id": application_id,
                "underwriting_details": uw_data
            }
        
        if decision == "COUNTER_OFFER":
            await self._emit_progress(
                application_id=application_id,
                progress_callback=progress_callback,
                event=PipelineEvent.COUNTER_OFFER_PENDING,
                stage=PipelineStage.DECISIONING,
                status="completed",
                message="Underwriting completed: counter offer generated",
                details={"decision": decision},
                is_terminal=True,
            )
            return {
                "status": "COUNTER_OFFER_PENDING",
                "application_id": application_id,
                "underwriting_details": uw_data
            }

        await self._emit_progress(
            application_id=application_id,
            progress_callback=progress_callback,
            event=PipelineEvent.APPLICATION_APPROVED,
            stage=PipelineStage.DECISIONING,
            status="completed",
            message="Underwriting completed: application approved",
            details={"decision": decision},
        )
            
        # 3. Disbursement Phase
        disburse_payload = map_decisioning_to_disbursement(decisioning_response=uw_data)

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
                json=disburse_payload
            )
            disburse_response.raise_for_status()
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
        
        return {
            "status": "DISBURSED",
            "application_id": application_id,
            "disbursement_receipt": disburse_data,
            "underwriting_details": uw_data
        }

    async def close(self):
        await self.http_client.aclose()
