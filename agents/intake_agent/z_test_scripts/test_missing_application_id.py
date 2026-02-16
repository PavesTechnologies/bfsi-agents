import pytest

# 👉 Use a valid file path
VALID_DL_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\barcode_working.jpg"


# ✅ 1️⃣ Missing application_id → Expect 422
def test_missing_application_id_returns_422(client):

    with open(VALID_DL_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/drivers-license",
            data={},  # ❌ Missing application_id
            files={"file": ("sample_dl.jpg", f, "image/jpeg")},
        )
    # print("test missing_application_id_returns_422 response:", response.json())
    
    assert response.status_code == 422


# ✅ 2️⃣ Empty application_id → Expect 422 or 400
def test_empty_application_id_returns_error(client):

    with open(VALID_DL_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/drivers-license",
            data={"application_id": ""},  # ❌ Empty string
            files={"file": ("sample_dl.jpg", f, "image/jpeg")},
        )

    # Depending on validation layer
    assert response.status_code in [400, 422]


# ✅ 3️⃣ Invalid UUID format → Expect 422 or 400
def test_invalid_uuid_format_returns_error(client):

    with open(VALID_DL_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/drivers-license",
            data={"application_id": "invalid-uuid"},
            files={"file": ("sample_dl.jpg", f, "image/jpeg")},
        )

    assert response.status_code in [400, 422]
