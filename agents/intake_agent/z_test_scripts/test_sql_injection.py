import pytest

VALID_DL_PATH = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\barcode_working.jpg"

SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE loan_application; --",
    "1 OR 1=1",
    "' OR 'a'='a",
    "'; SELECT * FROM users; --",
]


@pytest.mark.parametrize("malicious_input", SQL_INJECTION_PAYLOADS)
def test_sql_injection_protection(client, malicious_input):
    """
    Ensure SQL injection payloads are rejected.
    """

    with open(VALID_DL_PATH, "rb") as f:
        response = client.post(
            "/documents/upload/drivers-license",
            data={"application_id": malicious_input},
            files={"file": ("sample_dl.jpg", f, "image/jpeg")},
        )

    print(f"\nPayload: {malicious_input}")
    print("Response:", response.json())

    # Expect validation failure (never 200)
    assert response.status_code in [400, 422]
