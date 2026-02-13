import pytest
from httpx import AsyncClient, ASGITransport
from src.app import create_app
from uuid import uuid4
import os

# Create app instance
app = create_app()

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    # 'AsyncClient' with lifespan support
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://testserver"
    ) as c:
        yield c

def get_valid_payload(request_id=None):
    random_id = str(uuid4())[:8]
    return {
        "request_id": request_id or str(uuid4()),
        "callback_url": "http://example.com/callback",
        "loan_type": "personal",
        "credit_type": "individual",
        "loan_purpose": "debt_consolidation",
        "requested_amount": 5000.0,
        "requested_term_months": 36,
        "preferred_payment_day": 15,
        "origination_channel": "web",
        "applicants": [
            {
                "applicant_role": "primary",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "ssn_last4": str(uuid4().int)[:4],
                "email": f"john.{random_id}@example.com",
                "phone_number": "+11234567890",
                "gender": "MALE"
            }
        ]
    }

@pytest.mark.anyio
async def test_tc_i1_success_full_payload(client):
    """TC-I1: Success - Full Payload"""
    payload = get_valid_payload()
    # Add optional fields if any (already included in helper)
    response = await client.post("/loan_intake/submit_application", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "application_id" in data
    assert data["validation_issues"] == []

@pytest.mark.anyio
async def test_tc_i2_success_min_payload(client):
    """TC-I2: Success - Min Payload"""
    request_id = str(uuid4())
    payload = {
        "request_id": request_id,
        "callback_url": "http://example.com/callback",
        "loan_type": "personal",
        "credit_type": "individual",
        "loan_purpose": "debt_consolidation",
        "requested_amount": 5000.0,
        "requested_term_months": 36,
        "preferred_payment_day": 15,
        "origination_channel": "web",
        "applicants": [
                {
                    "first_name": "Min",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "applicant_role": "primary",
                    "ssn_last4": "1234",
                    "phone_number": "+11234567890",
                    "gender": "MALE"
                }
        ]
    }
    response = await client.post("/loan_intake/submit_application", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "application_id" in data

@pytest.mark.anyio
async def test_tc_i3_fail_missing_required(client):
    """TC-I3: Fail - Missing Required (Pydantic validation)"""
    payload = {
        "callback_url": "http://example.com/callback",
        "loan_type": "personal"
        # missing request_id, credit_type, etc.
    }
    response = await client.post("/loan_intake/submit_application", json=payload)
    assert response.status_code == 422

@pytest.mark.anyio
async def test_tc_i4_fail_invalid_amount(client):
    """TC-I4: Fail - Invalid Amount (requested_amount <= 0)"""
    payload = get_valid_payload()
    payload["requested_amount"] = 0
    response = await client.post("/loan_intake/submit_application", json=payload)
    # requested_amount has gt=0 in Pydantic schema
    assert response.status_code == 422 

@pytest.mark.anyio
async def test_tc_i5_fail_invalid_term(client):
    """TC-I5: Fail - Invalid Term (requested_term_months <= 1)"""
    payload = get_valid_payload()
    payload["requested_term_months"] = 1
    response = await client.post("/loan_intake/submit_application", json=payload)
    # Note: requested_term_months does not have gt=1 in Pydantic yet
    # If it fails here, it should be 400 or 422 depending on implementation
    # For now, we expect 400 if it's a blocking validation as per test case doc.
    # But if the code doesn't have it, this test will fail (returing 200).
    # We will implement the test expecting the requirement.
    assert response.status_code in [400, 422]

@pytest.mark.anyio
async def test_tc_i6_idempotency_duplicate(client):
    """TC-I6: Idempotency - Duplicate Submission"""
    payload = get_valid_payload()
    
    # First submission
    r1 = await client.post("/loan_intake/submit_application", json=payload)
    assert r1.status_code == 200
    id1 = r1.json()["application_id"]
    
    # Second submission with same request_id
    r2 = await client.post("/loan_intake/submit_application", json=payload)
    assert r2.status_code == 200
    id2 = r2.json()["application_id"]
    
    assert id1 == id2

@pytest.mark.anyio
async def test_tc_i7_non_blocking_bad_email(client):
    """TC-I7: Non-Blocking - Bad Email"""
    payload = get_valid_payload()
    payload["applicants"][0]["email"] = f"invalid-email-{uuid4().hex[:8]}"
    
    response = await client.post("/loan_intake/submit_application", json=payload)
    assert response.status_code == 200
    data = response.json()
    issues = data.get("validation_issues", [])
    assert any(issue["field"] == "applicant.email" for issue in issues)

@pytest.mark.anyio
async def test_tc_i8_non_blocking_underage(client):
    """TC-I8: Non-Blocking - Underage"""
    payload = get_valid_payload()
    # Applicant is 5 years old
    from datetime import datetime
    current_year = datetime.now().year
    payload["applicants"][0]["date_of_birth"] = f"{current_year - 5}-01-01"
    
    response = await client.post("/loan_intake/submit_application", json=payload)
    assert response.status_code == 200
    data = response.json()
    issues = data.get("validation_issues", [])
    assert any(issue["field"] == "applicant.dob" for issue in issues)
