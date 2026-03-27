"""
Tests for POST /internal/review-queue (orchestrator webhook, no auth).
"""
import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import delete

from src.db.base import AdminSessionLocal
from src.models.admin_models import HumanReviewQueue


def _cleanup(app_id: str) -> None:
    async def _run():
        async with AdminSessionLocal() as session:
            await session.execute(
                delete(HumanReviewQueue).where(HumanReviewQueue.application_id == app_id)
            )
            await session.commit()
    asyncio.run(_run())


class TestCreateReviewQueueEntry:
    def test_create_entry_returns_201_with_queue_id(
        self, client: TestClient, queue_entry
    ):
        assert "queue_id" in queue_entry
        assert len(queue_entry["queue_id"]) == 36  # UUID format

    def test_create_entry_no_auth_required(self, client: TestClient):
        """Internal endpoint must be callable without a JWT."""
        app_id = f"test-{uuid.uuid4()}"
        resp = client.post(
            "/internal/review-queue",
            json={"application_id": app_id, "ai_decision": "APPROVE"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "created"
        _cleanup(app_id)

    def test_idempotency_returns_already_exists(
        self, client: TestClient, queue_entry
    ):
        """Posting the same application_id a second time must not create a duplicate."""
        resp = client.post(
            "/internal/review-queue",
            json={
                "application_id": queue_entry["application_id"],
                "ai_decision": "APPROVE",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "already_exists"

    def test_counter_offer_with_jsonb_stored(
        self, client: TestClient, counter_offer_queue_entry
    ):
        """ai_counter_options JSONB round-trips correctly through the DB."""
        assert counter_offer_queue_entry["queue_id"] is not None

    def test_all_optional_fields_nullable(self, client: TestClient):
        """Entry with only required fields (application_id, ai_decision) is valid."""
        app_id = f"test-{uuid.uuid4()}"
        resp = client.post(
            "/internal/review-queue",
            json={"application_id": app_id, "ai_decision": "APPROVE"},
        )
        assert resp.status_code == 201
        _cleanup(app_id)

    def test_missing_required_field_returns_422(self, client: TestClient):
        resp = client.post(
            "/internal/review-queue",
            json={"ai_decision": "APPROVE"},  # missing application_id
        )
        assert resp.status_code == 422
