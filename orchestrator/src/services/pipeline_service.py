"""
Core Pipeline Service for Orchestration

Chains the APIs of Intake, KYC, Decisioning, and Disbursement agents.
"""

import httpx
import re
from typing import Dict, Any
from src.config import AgentConfig
from shared.data_mappers import (
    map_intake_to_kyc,
    map_to_underwriting,
    map_decisioning_to_disbursement
)
import json


class PipelineService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=AgentConfig.REQUEST_TIMEOUT_SECONDS)

    async def execute_full_pipeline(self, raw_application: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the end-to-end loan application flow starting with Intake.
        """
        print(json.dumps(raw_application, indent=2))
        # 1. Intake Phase
        intake_response = await self.http_client.post(
            f"{AgentConfig.INTAKE_AGENT_URL}/loan_intake/submit_application",
            json=raw_application
        )
        intake_response.raise_for_status()
        intake_data = intake_response.json()
        
        application_id = intake_data.get("application_id")
        
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
        kyc_payload = map_intake_to_kyc(
            application_id=application_id,
            applicant=applicant_data,
            idempotency_key=f"kyc_{application_id}"
        )

        
        print((json.dumps(kyc_payload, indent=2)))

        kyc_response = await self.http_client.post(
            f"{AgentConfig.KYC_AGENT_URL}/verify",
            json=kyc_payload
        )
        kyc_response.raise_for_status()
        kyc_data = kyc_response.json()

        print(json.dumps(kyc_data, indent=2))
        
        if kyc_data.get("status") != "PASS":
            return {
                "status": "REJECTED_AT_KYC",
                "application_id": application_id,
                "kyc_details": kyc_data
            }

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
        
        uw_response = await self.http_client.post(
            f"{AgentConfig.DECISIONING_AGENT_URL}/underwrite",
            json=underwriting_payload
        )
        uw_response.raise_for_status()
        uw_data = uw_response.json()
        
        decision = uw_data.get("decision")
        
        if decision == "DECLINE":
            return {
                "status": "DECLINED",
                "application_id": application_id,
                "underwriting_details": uw_data
            }
        
        if decision == "COUNTER_OFFER":
            return {
                "status": "COUNTER_OFFER_PENDING",
                "application_id": application_id,
                "underwriting_details": uw_data
            }
            
        # 3. Disbursement Phase
        disburse_payload = map_decisioning_to_disbursement(decisioning_response=uw_data)
        
        disburse_response = await self.http_client.post(
            f"{AgentConfig.DISBURSEMENT_AGENT_URL}/disburse",
            json=disburse_payload
        )
        disburse_response.raise_for_status()
        disburse_data = disburse_response.json()
        
        return {
            "status": "DISBURSED",
            "application_id": application_id,
            "disbursement_receipt": disburse_data,
            "underwriting_details": uw_data
        }

    async def close(self):
        await self.http_client.aclose()
