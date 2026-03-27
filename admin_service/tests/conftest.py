"""
Shared fixtures for admin_service tests.

Uses starlette's synchronous TestClient (backed by anyio in a background thread)
to avoid event-loop-per-test conflicts with asyncpg on Windows. All test
functions are therefore plain `def`, not `async def`.

Each test that creates DB rows gets a unique application_id and a cleanup
fixture that deletes those rows after the test using asyncio.run().
"""
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from src.app import create_app
from src.db.base import AdminSessionLocal
from src.models.admin_models import HumanReviewDecision, HumanReviewQueue


# ---------------------------------------------------------------------------
# App + HTTP client  (session scope — one lifespan for the whole test run)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def admin_app():
    return create_app()


@pytest.fixture(scope="session")
def client(admin_app):
    """Single TestClient shared across all tests in the session."""
    with TestClient(admin_app, raise_server_exceptions=True) as tc:
        yield tc


# ---------------------------------------------------------------------------
# Auth  (session scope — login once, reuse token everywhere)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def auth_token(client):
    resp = client.post(
        "/auth/login",
        json={"email": "admin@bank.com", "password": "changeme"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token['access_token']}"}


# ---------------------------------------------------------------------------
# Per-test helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def app_id():
    """Unique fake application_id per test (test- prefix for easy cleanup)."""
    return f"test-{uuid.uuid4()}"


def _delete_queue_rows(application_id: str) -> None:
    """Synchronous teardown helper: delete test rows using asyncio.run()."""
    async def _run():
        async with AdminSessionLocal() as session:
            await session.execute(
                delete(HumanReviewDecision).where(
                    HumanReviewDecision.application_id == application_id
                )
            )
            await session.execute(
                delete(HumanReviewQueue).where(
                    HumanReviewQueue.application_id == application_id
                )
            )
            await session.commit()

    asyncio.run(_run())


@pytest.fixture
def queue_entry(client, app_id):
    """
    Create a PENDING HumanReviewQueue row and yield its IDs.
    Deletes the row (and any decision records) after the test.
    """
    resp = client.post(
        "/internal/review-queue",
        json={
            "application_id": app_id,
            "ai_decision": "APPROVE",
            "ai_risk_tier": "A",
            "ai_risk_score": 88.5,
            "ai_suggested_amount": 50000.0,
            "ai_suggested_rate": 7.5,
            "ai_suggested_tenure": 36,
        },
    )
    assert resp.status_code == 201, resp.text
    queue_id = resp.json()["queue_id"]
    yield {"queue_id": queue_id, "application_id": app_id}
    _delete_queue_rows(app_id)


@pytest.fixture
def counter_offer_queue_entry(client, app_id):
    """PENDING queue entry with COUNTER_OFFER decision and JSONB counter options."""
    resp = client.post(
        "/internal/review-queue",
        json={
            "application_id": app_id,
            "ai_decision": "COUNTER_OFFER",
            "ai_risk_tier": "B",
            "ai_risk_score": 62.1,
            "ai_suggested_amount": 30000.0,
            "ai_suggested_rate": 11.0,
            "ai_suggested_tenure": 48,
            "ai_counter_options": {
                "generated_options": [
                    {
                        "offer_id": "OPT_1",
                        "principal_amount": 30000,
                        "tenure_months": 48,
                        "interest_rate": 11.0,
                        "monthly_emi": 776.0,
                        "label": "Recommended",
                    }
                ]
            },
        },
    )
    assert resp.status_code == 201, resp.text
    queue_id = resp.json()["queue_id"]
    yield {"queue_id": queue_id, "application_id": app_id}
    _delete_queue_rows(app_id)
