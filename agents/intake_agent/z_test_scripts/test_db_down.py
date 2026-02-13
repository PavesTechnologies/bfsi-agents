import pytest
from unittest.mock import patch
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

VALID_DL_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\barcode_working.jpg"
VALID_APPLICATION_ID = "a41b53c5-1975-4dcb-9307-c2c514138b2f"


def mock_db_failure(*args, **kwargs):
    raise SQLAlchemyError("Database connection failed")


@patch(
    "src.services.intake_services.document_upload_service.LoanInfoDAO.get_loan_application_by_id",
    side_effect=mock_db_failure,
)
def test_submit_application_when_db_down(mock_method, client):
    """
    Simulate DB unreachable scenario.
    Expect graceful 500 response.
    """

    with open(VALID_DL_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/drivers-license",
            data={"application_id": VALID_APPLICATION_ID},
            files={"file": ("sample_dl.jpg", f, "image/jpeg")},
        )

    print("DB Down Response:", response.json())

    assert response.status_code == 500
