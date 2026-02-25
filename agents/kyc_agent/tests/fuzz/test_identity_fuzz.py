import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from src.app import create_app

app = create_app()


# ---------- FIXTURE ----------
@pytest.fixture
def client():
    return TestClient(app)


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

name_strategy = st.one_of(
    st.text(min_size=0, max_size=100),
    st.none(),
)

uuid_strategy = st.one_of(
    st.uuids().map(str),
    st.text(min_size=0, max_size=50),
    st.none(),
)


# ---------- ADDRESS STRATEGY ----------

address_strategy = st.one_of(
    st.fixed_dictionaries(
        {
            "line1": st.text(min_size=0, max_size=100),
            "line2": st.text(min_size=0, max_size=100),
            "city": st.text(min_size=0, max_size=50),
            "state": st.text(min_size=0, max_size=20),
            "zip": st.text(min_size=0, max_size=10),
        }
    ),
    st.none(),
)


# ---------- FUZZ TEST ----------

@given(
    applicant_id=uuid_strategy,
    full_name=name_strategy,
    email=email_strategy,
    phone=phone_strategy,
    ssn=ssn_strategy,
    dob=dob_strategy,
    address=address_strategy,
    idempotency_key=uuid_strategy,
)
@settings(max_examples=50)
def test_verify_identity_fuzz(
    applicant_id,
    full_name,
    email,
    phone,
    ssn,
    dob,
    address,
    idempotency_key,
):
    app = create_app()
    client = TestClient(app)

    payload = {
        "applicant_id": applicant_id,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "ssn": ssn,
        "dob": dob,
        "address": address,
        "idempotency_key": idempotency_key,
    }
    print(f"Testing with payload: {payload}")
    response = client.post("/kyc/verify", json=payload)
    assert response.status_code <500
