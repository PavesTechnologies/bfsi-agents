"""
End-to-End Mock Integration Test for BFSI Agents Pipeline
"""

import asyncio
import httpx
import uuid
import json


async def test_run():
    application_id = str(uuid.uuid4())
    print(f"🚀 Starting End-to-End Pipeline Mock Test for App ID: {application_id}")

    # 1. Mock Intake Response
    mock_intake_response = {
        "application_id": application_id,
        "timestamp": "2026-03-05T12:00:00Z",
        "validation_issues": []
    }

    # 2. Mock Applicant Data
    mock_applicant_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "ssn_no": "000000000",
        "email": "john.doe@example.com",
        "phone_number": "555-0100",
        "addresses": [
            {
                "address_type": "current",
                "address_line1": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62701"
            }
        ],
        "incomes": [
            {
                "monthly_amount": 10000.0,
                "income_type": "base_salary"
            }
        ]
    }

    print("\n📦 Request Payload:")
    payload = {
        "raw_application": {
            "request_id": str(uuid.uuid4()),
            "callback_url": "https://example.com/callback",
            "loan_type": "personal",
            "credit_type": "individual",
            "loan_purpose": "debt_consolidation",
            "requested_amount": 100000.0,
            "requested_term_months": 36,
            "preferred_payment_day": 1,
            "origination_channel": "web",
            "applicants": [mock_applicant_data]
        }
    }
    print(json.dumps(payload, indent=2))

    print("\n⏳ Note: To run this test live, the Orchestrator + 4 Agents must be running.")
    print("Run: curl -X POST http://localhost:8004/trigger_pipeline -H 'Content-Type: application/json' -d '...'")

if __name__ == "__main__":
    asyncio.run(test_run())
