"""
Tests for /config/* endpoints (Phase 4 — Configuration & Policy Management).

All mutations are append-only versioned. PUT tests create new rows and the
teardown fixture restores the original active row so subsequent tests see
consistent seed data.
"""
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from src.db.base import AdminSessionLocal
from src.models.admin_models import LoanPolicy, RiskTierConfig


# ---------------------------------------------------------------------------
# Teardown helpers — restore seed data after mutation tests
# ---------------------------------------------------------------------------

def _restore_tier(tier: str, original_id: str) -> None:
    """Deactivate test rows and re-activate the original seed row."""
    async def _run():
        async with AdminSessionLocal() as session:
            await session.execute(
                update(RiskTierConfig)
                .where(RiskTierConfig.tier == tier, RiskTierConfig.is_active == True)
                .values(is_active=False)
            )
            await session.execute(
                update(RiskTierConfig)
                .where(RiskTierConfig.id == original_id)
                .values(is_active=True)
            )
            await session.commit()
    asyncio.run(_run())


def _restore_policy(policy_key: str, original_id: str) -> None:
    """Deactivate test rows and re-activate the original seed row."""
    async def _run():
        async with AdminSessionLocal() as session:
            await session.execute(
                update(LoanPolicy)
                .where(LoanPolicy.policy_key == policy_key, LoanPolicy.is_active == True)
                .values(is_active=False)
            )
            await session.execute(
                update(LoanPolicy)
                .where(LoanPolicy.id == original_id)
                .values(is_active=True)
            )
            await session.commit()
    asyncio.run(_run())


# ---------------------------------------------------------------------------
# GET /config/risk-tiers
# ---------------------------------------------------------------------------

class TestGetRiskTiers:
    def test_returns_four_tiers(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4
        tiers = {item["tier"] for item in data}
        assert tiers == {"A", "B", "C", "F"}

    def test_all_are_active(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers", headers=auth_headers)
        for item in resp.json():
            assert item["is_active"] is True

    def test_tier_a_seed_values(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers", headers=auth_headers)
        tier_a = next(i for i in resp.json() if i["tier"] == "A")
        assert tier_a["min_credit_score"] == 750
        assert tier_a["max_dti_ratio"] == pytest.approx(0.35)
        assert tier_a["max_loan_amount"] == pytest.approx(500000.0)

    def test_schema_fields_present(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers", headers=auth_headers)
        item = resp.json()[0]
        for field in (
            "id", "tier", "min_interest_rate", "max_interest_rate",
            "default_interest_rate", "max_loan_amount", "min_loan_amount",
            "min_credit_score", "max_dti_ratio", "is_active",
            "effective_from", "created_at",
        ):
            assert field in item, f"Missing field: {field}"

    def test_requires_auth(self, client: TestClient):
        resp = client.get("/config/risk-tiers")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /config/risk-tiers/history
# ---------------------------------------------------------------------------

class TestGetRiskTierHistory:
    def test_returns_paginated_response(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers/history", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "items" in data
        assert data["total"] >= 4  # at least the 4 seed rows

    def test_filter_by_tier(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers/history?tier=B", headers=auth_headers)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["tier"] == "B"

    def test_invalid_tier_returns_403(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers/history?tier=X", headers=auth_headers)
        assert resp.status_code == 403

    def test_pagination(self, client: TestClient, auth_headers):
        resp = client.get(
            "/config/risk-tiers/history?page=1&page_size=2", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2

    def test_requires_manager_role(self, client: TestClient, auth_headers):
        """Admin user passes (ADMIN >= MANAGER)."""
        resp = client.get("/config/risk-tiers/history", headers=auth_headers)
        assert resp.status_code == 200

    def test_requires_auth(self, client: TestClient):
        resp = client.get("/config/risk-tiers/history")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /config/risk-tiers/{tier}
# ---------------------------------------------------------------------------

class TestUpdateRiskTier:
    def test_update_tier_b_creates_new_row(self, client: TestClient, auth_headers):
        # Capture current active B row id for teardown
        resp = client.get("/config/risk-tiers", headers=auth_headers)
        original = next(i for i in resp.json() if i["tier"] == "B")
        original_id = original["id"]

        try:
            resp = client.put(
                "/config/risk-tiers/B",
                headers=auth_headers,
                json={
                    "default_interest_rate": 11.5,
                    "min_interest_rate": 9.5,
                    "max_interest_rate": 14.5,
                    "max_loan_amount": 200000,
                    "min_loan_amount": 5000,
                    "min_credit_score": 660,
                    "max_dti_ratio": 0.43,
                    "effective_from": "2026-04-01T00:00:00Z",
                    "notes": "Test update",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["tier"] == "B"
            assert data["is_active"] is True
            assert data["default_interest_rate"] == pytest.approx(11.5)
            assert data["notes"] == "Test update"
            assert data["id"] != original_id  # new row created
        finally:
            _restore_tier("B", original_id)

    def test_old_row_deactivated_after_update(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers", headers=auth_headers)
        original = next(i for i in resp.json() if i["tier"] == "C")
        original_id = original["id"]

        try:
            client.put(
                "/config/risk-tiers/C",
                headers=auth_headers,
                json={
                    "default_interest_rate": 17.0,
                    "min_interest_rate": 14.0,
                    "max_interest_rate": 20.0,
                    "max_loan_amount": 75000,
                    "min_loan_amount": 1000,
                    "min_credit_score": 580,
                    "max_dti_ratio": 0.50,
                    "effective_from": "2026-04-01T00:00:00Z",
                },
            )
            # Only one active C row should exist
            history = client.get(
                "/config/risk-tiers/history?tier=C", headers=auth_headers
            ).json()
            active_rows = [i for i in history["items"] if i["is_active"]]
            assert len(active_rows) == 1
        finally:
            _restore_tier("C", original_id)

    def test_history_grows_after_update(self, client: TestClient, auth_headers):
        resp = client.get("/config/risk-tiers", headers=auth_headers)
        original = next(i for i in resp.json() if i["tier"] == "F")
        original_id = original["id"]

        before = client.get(
            "/config/risk-tiers/history?tier=F", headers=auth_headers
        ).json()["total"]

        try:
            client.put(
                "/config/risk-tiers/F",
                headers=auth_headers,
                json={
                    "default_interest_rate": 24.5,
                    "min_interest_rate": 20.0,
                    "max_interest_rate": 28.0,
                    "max_loan_amount": 25000,
                    "min_loan_amount": 500,
                    "min_credit_score": 500,
                    "max_dti_ratio": 0.55,
                    "effective_from": "2026-04-01T00:00:00Z",
                },
            )
            after = client.get(
                "/config/risk-tiers/history?tier=F", headers=auth_headers
            ).json()["total"]
            assert after == before + 1
        finally:
            _restore_tier("F", original_id)

    def test_invalid_rate_ordering_rejected(self, client: TestClient, auth_headers):
        """default_interest_rate > max_interest_rate must be rejected.
        Pydantic validates the ordering at schema level → 422 Unprocessable Entity."""
        resp = client.put(
            "/config/risk-tiers/A",
            headers=auth_headers,
            json={
                "default_interest_rate": 15.0,  # > max
                "min_interest_rate": 6.0,
                "max_interest_rate": 10.0,
                "max_loan_amount": 500000,
                "min_loan_amount": 10000,
                "min_credit_score": 750,
                "max_dti_ratio": 0.35,
                "effective_from": "2026-04-01T00:00:00Z",
            },
        )
        assert resp.status_code == 422

    def test_unknown_tier_returns_404(self, client: TestClient, auth_headers):
        resp = client.put(
            "/config/risk-tiers/Z",
            headers=auth_headers,
            json={
                "default_interest_rate": 10.0,
                "min_interest_rate": 8.0,
                "max_interest_rate": 12.0,
                "max_loan_amount": 100000,
                "min_loan_amount": 1000,
                "min_credit_score": 600,
                "max_dti_ratio": 0.40,
                "effective_from": "2026-04-01T00:00:00Z",
            },
        )
        assert resp.status_code == 404

    def test_requires_auth(self, client: TestClient):
        resp = client.put(
            "/config/risk-tiers/A",
            json={
                "default_interest_rate": 7.5,
                "min_interest_rate": 6.0,
                "max_interest_rate": 10.0,
                "max_loan_amount": 500000,
                "min_loan_amount": 10000,
                "min_credit_score": 750,
                "max_dti_ratio": 0.35,
                "effective_from": "2026-04-01T00:00:00Z",
            },
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /config/policies
# ---------------------------------------------------------------------------

class TestGetPolicies:
    def test_returns_all_active_policies(self, client: TestClient, auth_headers):
        resp = client.get("/config/policies", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 6
        for item in data:
            assert item["is_active"] is True

    def test_filter_by_category(self, client: TestClient, auth_headers):
        resp = client.get("/config/policies?category=UNDERWRITING", headers=auth_headers)
        assert resp.status_code == 200
        for item in resp.json():
            assert item["category"] == "UNDERWRITING"

    def test_schema_fields_present(self, client: TestClient, auth_headers):
        resp = client.get("/config/policies", headers=auth_headers)
        item = resp.json()[0]
        for field in (
            "id", "policy_key", "policy_value", "description",
            "category", "is_active", "effective_from", "created_at",
        ):
            assert field in item, f"Missing field: {field}"

    def test_policy_value_is_jsonb(self, client: TestClient, auth_headers):
        resp = client.get("/config/policies", headers=auth_headers)
        for item in resp.json():
            assert isinstance(item["policy_value"], dict)
            assert "value" in item["policy_value"]

    def test_requires_auth(self, client: TestClient):
        resp = client.get("/config/policies")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /config/policies/history
# ---------------------------------------------------------------------------

class TestGetPolicyHistory:
    def test_returns_paginated_response(self, client: TestClient, auth_headers):
        resp = client.get("/config/policies/history", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data and "items" in data
        assert data["total"] >= 6

    def test_filter_by_policy_key(self, client: TestClient, auth_headers):
        resp = client.get(
            "/config/policies/history?policy_key=KYC_CONFIDENCE_THRESHOLD",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["policy_key"] == "KYC_CONFIDENCE_THRESHOLD"

    def test_pagination(self, client: TestClient, auth_headers):
        resp = client.get(
            "/config/policies/history?page=1&page_size=3", headers=auth_headers
        )
        data = resp.json()
        assert data["page_size"] == 3
        assert len(data["items"]) <= 3

    def test_requires_auth(self, client: TestClient):
        resp = client.get("/config/policies/history")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /config/policies/{policy_key}
# ---------------------------------------------------------------------------

class TestUpdatePolicy:
    def test_update_policy_creates_new_row(self, client: TestClient, auth_headers):
        resp = client.get("/config/policies", headers=auth_headers)
        original = next(i for i in resp.json() if i["policy_key"] == "MIN_INCOME_MONTHLY")
        original_id = original["id"]

        try:
            resp = client.put(
                "/config/policies/MIN_INCOME_MONTHLY",
                headers=auth_headers,
                json={
                    "policy_value": {"value": 2500, "unit": "USD"},
                    "effective_from": "2026-04-01T00:00:00Z",
                    "notes": "Raised minimum income threshold",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["policy_key"] == "MIN_INCOME_MONTHLY"
            assert data["is_active"] is True
            assert data["policy_value"]["value"] == 2500
            assert data["id"] != original_id
            # description + category preserved from old row
            assert data["description"] == original["description"]
            assert data["category"] == original["category"]
        finally:
            _restore_policy("MIN_INCOME_MONTHLY", original_id)

    def test_old_policy_deactivated_after_update(self, client: TestClient, auth_headers):
        resp = client.get("/config/policies", headers=auth_headers)
        original = next(i for i in resp.json() if i["policy_key"] == "ORIGINATION_FEE_PERCENT")
        original_id = original["id"]

        try:
            client.put(
                "/config/policies/ORIGINATION_FEE_PERCENT",
                headers=auth_headers,
                json={
                    "policy_value": {"value": 2.5, "unit": "percent"},
                    "effective_from": "2026-04-01T00:00:00Z",
                },
            )
            history = client.get(
                "/config/policies/history?policy_key=ORIGINATION_FEE_PERCENT",
                headers=auth_headers,
            ).json()
            active_rows = [i for i in history["items"] if i["is_active"]]
            assert len(active_rows) == 1
        finally:
            _restore_policy("ORIGINATION_FEE_PERCENT", original_id)

    def test_history_grows_after_update(self, client: TestClient, auth_headers):
        resp = client.get("/config/policies", headers=auth_headers)
        original = next(i for i in resp.json() if i["policy_key"] == "MAX_LOAN_PERSONAL")
        original_id = original["id"]

        before = client.get(
            "/config/policies/history?policy_key=MAX_LOAN_PERSONAL",
            headers=auth_headers,
        ).json()["total"]

        try:
            client.put(
                "/config/policies/MAX_LOAN_PERSONAL",
                headers=auth_headers,
                json={
                    "policy_value": {"value": 600000, "unit": "USD"},
                    "effective_from": "2026-04-01T00:00:00Z",
                },
            )
            after = client.get(
                "/config/policies/history?policy_key=MAX_LOAN_PERSONAL",
                headers=auth_headers,
            ).json()["total"]
            assert after == before + 1
        finally:
            _restore_policy("MAX_LOAN_PERSONAL", original_id)

    def test_unknown_policy_key_returns_404(self, client: TestClient, auth_headers):
        resp = client.put(
            "/config/policies/NONEXISTENT_KEY",
            headers=auth_headers,
            json={
                "policy_value": {"value": 999},
                "effective_from": "2026-04-01T00:00:00Z",
            },
        )
        assert resp.status_code == 404

    def test_requires_auth(self, client: TestClient):
        resp = client.put(
            "/config/policies/MAX_LOAN_PERSONAL",
            json={
                "policy_value": {"value": 500000, "unit": "USD"},
                "effective_from": "2026-04-01T00:00:00Z",
            },
        )
        assert resp.status_code == 401
