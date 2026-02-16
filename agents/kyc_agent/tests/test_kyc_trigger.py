import pytest
from uuid import uuid4


# --------------------------------------------------------
# Payload Factory
# --------------------------------------------------------

def build_payload(idempotency_key: str):
    return {
        "applicant_id": str(uuid4()),
        "full_name": "John Michael Doe",
        "dob": "1990-05-14",
        "ssn": "123456789",
        "address": {
            "line1": "742 Evergreen Terrace",
            "line2": "Apt 5B",
            "city": "Springfield",
            "state": "IL",
            "zip": "62704"
        },
        "phone": "+12175551234",
        "email": "john.doe@example.com",
        "idempotency_key": idempotency_key
    }


# --------------------------------------------------------
# Test: Successful Trigger
# --------------------------------------------------------

def test_trigger_kyc_success(client):
    payload = build_payload("test-key-001")

    response = client.post("/kyc/trigger", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert "attempt_id" in data
    assert data["kyc_status"] == "PENDING"


# --------------------------------------------------------
# Test: Idempotent Retry (Same Payload)
# --------------------------------------------------------

def test_trigger_kyc_idempotent_retry(client):
    payload = build_payload("test-key-002")

    first = client.post("/kyc/trigger", json=payload)
    second = client.post("/kyc/trigger", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


# --------------------------------------------------------
# Test: Idempotency Conflict (Same Key, Different Payload)
# --------------------------------------------------------

def test_trigger_kyc_idempotency_conflict(client):
    key = "test-key-003"

    payload1 = build_payload(key)
    payload2 = build_payload(key)

    # Modify SSN → payload hash mismatch
    payload2["ssn"] = "987654321"

    first = client.post("/kyc/trigger", json=payload1)
    second = client.post("/kyc/trigger", json=payload2)

    assert first.status_code == 200
    assert second.status_code == 409


# --------------------------------------------------------
# Test: Invalid SSN (Validation Error)
# --------------------------------------------------------

def test_trigger_kyc_invalid_ssn(client):
    payload = build_payload("test-key-004")
    payload["ssn"] = "123"  # Invalid (not 9 digits)

    response = client.post("/kyc/trigger", json=payload)

    assert response.status_code == 422