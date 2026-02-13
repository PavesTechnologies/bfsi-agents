import pytest
from uuid import uuid4

# Use a valid application ID from DB
VALID_APPLICATION_ID = "a41b53c5-1975-4dcb-9307-c2c514138b2f"
VALID_REVIEWER_ID = str(uuid4())


# ---------------------------------------------------------
# ✅ 1️⃣ Valid Approval
# ---------------------------------------------------------
def test_valid_approval(client):
    payload = {
        "application_id": VALID_APPLICATION_ID,
        "reviewer_id": VALID_REVIEWER_ID,
        "decision": "APPROVE",
        "reason_codes": ["DOC_VERIFIED"],
        "comments": "All documents verified."
    }

    response = client.post("/human-review/submit", json=payload)
    assert response.status_code == 200


# ---------------------------------------------------------
# ✅ 2️⃣ Valid Rejection
# ---------------------------------------------------------
def test_valid_rejection(client):
    payload = {
        "application_id": VALID_APPLICATION_ID,
        "reviewer_id": VALID_REVIEWER_ID,
        "decision": "REJECT",
        "reason_codes": ["ID_MISMATCH"],
        "comments": "Identity mismatch found."
    }

    response = client.post("/human-review/submit", json=payload)
    assert response.status_code == 200


# ---------------------------------------------------------
# ✅ 3️⃣ Approve Without Reasons
# ---------------------------------------------------------
def test_approve_without_reasons(client):
    payload = {
        "application_id": VALID_APPLICATION_ID,
        "reviewer_id": VALID_REVIEWER_ID,
        "decision": "APPROVE",
        "reason_codes": [],
        "comments": "Approved."
    }

    response = client.post("/human-review/submit", json=payload)
    assert response.status_code == 200


# ---------------------------------------------------------
# ✅ 4️⃣ Reject With Multiple Reasons
# ---------------------------------------------------------
def test_reject_with_multiple_reasons(client):
    payload = {
        "application_id": VALID_APPLICATION_ID,
        "reviewer_id": VALID_REVIEWER_ID,
        "decision": "REJECT",
        "reason_codes": ["BLURRY_DOC", "NAME_MISMATCH"],
        "comments": "Multiple validation failures."
    }

    response = client.post("/human-review/submit", json=payload)
    assert response.status_code == 200


# ---------------------------------------------------------
# ✅ 5️⃣ Long Comments (1000+ chars)
# ---------------------------------------------------------
def test_long_comments(client):
    payload = {
        "application_id": VALID_APPLICATION_ID,
        "reviewer_id": VALID_REVIEWER_ID,
        "decision": "APPROVE",
        "reason_codes": [],
        "comments": "A" * 1200
    }

    response = client.post("/human-review/submit", json=payload)
    assert response.status_code == 200


# ---------------------------------------------------------
# ❌ 6️⃣ Missing application_id
# ---------------------------------------------------------
def test_missing_application_id(client):
    payload = {
        "reviewer_id": VALID_REVIEWER_ID,
        "decision": "APPROVE",
        "reason_codes": [],
        "comments": "Missing application id."
    }

    response = client.post("/human-review/submit", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------
# ❌ 7️⃣ Invalid UUID
# ---------------------------------------------------------
def test_invalid_uuid(client):
    payload = {
        "application_id": "invalid-uuid",
        "reviewer_id": VALID_REVIEWER_ID,
        "decision": "APPROVE",
        "reason_codes": [],
        "comments": "Invalid UUID."
    }

    response = client.post("/human-review/submit", json=payload)
    assert response.status_code == 422


# -----------
