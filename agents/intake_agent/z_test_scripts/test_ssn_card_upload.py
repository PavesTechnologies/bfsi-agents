import pytest
from pathlib import Path

APPLICATION_ID = "a41b53c5-1975-4dcb-9307-c2c514138b2f"

# 👉 Update these paths properly
VALID_SSN_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\ssn.jpg"
INVALID_SSN_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\USA.jpg"
UNSUPPORTED_FILE_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\Sri_Charan_credentials.csv"


# ✅ 1️⃣ Invalid SSN Card → expect 400
def test_invalid_ssn_card_returns_400(client):

    with open(INVALID_SSN_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/ssn-card",
            data={"application_id": APPLICATION_ID},
            files={"file": ("invalid_ssn.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 400


# ✅ 2️⃣ Valid SSN Card → expect 200
def test_valid_ssn_card_returns_200(client):

    with open(VALID_SSN_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/ssn-card",
            data={"application_id": APPLICATION_ID},
            files={"file": ("valid_ssn.jpg", f, "image/jpeg")},
        )

    assert response.status_code in [200, 201]


# ✅ 3️⃣ Unsupported File Type → expect 415
def test_unsupported_file_type_returns_415(client):

    with open(UNSUPPORTED_FILE_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/ssn-card",
            data={"application_id": APPLICATION_ID},
            files={"file": ("invalid_file.csv", f, "text/csv")},
        )

    assert response.status_code == 415
