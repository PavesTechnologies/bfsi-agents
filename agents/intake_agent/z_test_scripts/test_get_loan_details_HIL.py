import pytest
from uuid import uuid4

# Use a real existing UUID from your DB for success test
VALID_APPLICATION_ID = "01ea5aee-539e-42ce-a4ce-07a2bbb5e209"

# Generate a random UUID (not in DB)
NON_EXISTING_APPLICATION_ID = str(uuid4())


# ✅ 1️⃣ Valid Application ID
def test_get_loan_valid_application_id(client):
    response = client.get(f"/loans/{VALID_APPLICATION_ID}")

    assert response.status_code == 200
    assert response.json() is not None


# ✅ 2️⃣ Non-Existing Application ID
def test_get_loan_non_existing_application_id(client):
    response = client.get(f"/loans/{NON_EXISTING_APPLICATION_ID}")

    # Based on your implementation (you mentioned 400 Not Found)
    assert response.status_code in [400, 404]


# ✅ 3️⃣ Invalid UUID Format
def test_get_loan_invalid_uuid_format(client):
    response = client.get("/loans/invalid-uuid")

    assert response.status_code == 422


# ✅ 4️⃣ Empty UUID
def test_get_loan_empty_uuid(client):
    response = client.get("/loans/")

    # FastAPI path param missing → 404 or 422 depending on router
    assert response.status_code in [404, 422]


# ✅ 5️⃣ SQL Injection Attempt
def test_get_loan_sql_injection_attempt(client):
    response = client.get("/loans/1 OR 1=1")

    # UUID validation should block this
    assert response.status_code == 422


# ✅ 6️⃣ Extremely Long String
def test_get_loan_extremely_long_string(client):
    long_string = "a" * 250
    response = client.get(f"/loans/{long_string}")

    assert response.status_code == 422
