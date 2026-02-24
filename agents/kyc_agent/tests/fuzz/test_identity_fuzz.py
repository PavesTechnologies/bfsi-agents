import pytest
from hypothesis import given, strategies as st
from fastapi.testclient import TestClient
from src.app import create_app


# ---------- PII STRATEGIES ----------

email_strategy = st.one_of(
    st.emails(),
    st.text(min_size=0, max_size=100),
    st.none(),
)

phone_strategy = st.one_of(
    st.from_regex(r"^\+?[0-9]{0,20}$"),
    st.text(min_size=0, max_size=50),
    st.none(),
)

ssn_strategy = st.one_of(
    st.from_regex(r"^\d{3}-?\d{2}-?\d{4}$"),
    st.text(min_size=0, max_size=50),
    st.none(),
)

dob_strategy = st.one_of(
    st.dates().map(str),
    st.text(min_size=0, max_size=50),
    st.none(),
)


# ---------- FUZZ TEST ----------

@given(
    applicant_id=st.one_of(st.text(min_size=0, max_size=50), st.none()),
    email=email_strategy,
    phone=phone_strategy,
    ssn=ssn_strategy,
    dob=dob_strategy,
)
# @pytest.mark.asyncio
def test_verify_identity_fuzz(
    
    client: TestClient,
    applicant_id,
    email,
    phone,
    ssn,
    dob,
):
    payload = {
        "applicant_id": applicant_id,
        "email": email,
        "phone": phone,
        "ssn": ssn,
        "dob": dob,
    }

    response = client.post("/kyc/verify", json=payload)

    # 🔒 MUST never crash
    assert response.status_code< 500

MALICIOUS_INPUTS = [
    "' OR 1=1 --",
    "'; DROP TABLE users; --",
    '{"$ne": null}',
    "<script>alert(1)</script>",
    "../../etc/passwd",
    "\x00\x01\x02",
]

# @pytest.mark.asyncio
@pytest.mark.parametrize("bad_input", MALICIOUS_INPUTS)
def test_verify_identity_injection(client, bad_input):
    payload = {
        "applicant_id": bad_input,
        "email": bad_input,
        "phone": bad_input,
        "ssn": bad_input,
        "dob": bad_input,
    }

    response =client.post("/kyc/verify", json=payload)

    assert response.status_code != 500
    assert response.status_code in (200, 400, 422)