import pytest
from pathlib import Path

APPLICATION_ID = "a41b53c5-1975-4dcb-9307-c2c514138b2f"

# Update these paths to your real test files
VALID_DL_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\barcode_working.jpg"
INVALID_DL_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\ssn2.jpg"
UNSUPPORTED_FILE_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\Sri_Charan_credentials.csv"


# ✅ 1. Invalid document (validation should fail → 400)
def test_invalid_drivers_license_returns_400(client):

    with open(INVALID_DL_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/drivers-license",
            data={"application_id": APPLICATION_ID},
            files={"file": ("invalid_dl.jpg", f, "image/jpeg")},
        )

    assert response.status_code == 400


# ✅ 2. Valid document (validation should pass → 200)
def test_valid_drivers_license_returns_200(client):

    with open(VALID_DL_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/drivers-license",
            data={"application_id": APPLICATION_ID},
            files={"file": ("valid_dl.jpg", f, "image/jpeg")},
        )

    assert response.status_code in [200, 201]


# ✅ 3. Unsupported document type (wrong MIME → 415)
def test_unsupported_file_type_returns_415(client):

    with open(UNSUPPORTED_FILE_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/drivers-license",
            data={"application_id": APPLICATION_ID},
            files={"file": ("file.csv", f, "text/csv")},
        )

    assert response.status_code == 415
