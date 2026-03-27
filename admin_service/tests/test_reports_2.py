import re
import pytest
from fastapi.testclient import TestClient


class TestDisbursementsReport:
    def test_returns_200_with_correct_shape(self, client: TestClient, auth_headers):
        response = client.get("/reports/disbursements", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "chart_data" in data
        assert isinstance(data["chart_data"], list)
        assert "summary" in data
        summary = data["summary"]
        for key in ("total_count", "total_amount", "avg_loan_amount", "avg_interest_rate", "avg_tenure_months", "total_interest_income"):
            assert key in summary, f"Missing summary key: {key}"

    def test_summary_fields_non_negative(self, client: TestClient, auth_headers):
        response = client.get("/reports/disbursements", headers=auth_headers)
        assert response.status_code == 200
        summary = response.json()["summary"]
        for key in ("total_count", "total_amount", "avg_loan_amount", "avg_interest_rate", "avg_tenure_months", "total_interest_income"):
            assert summary[key] >= 0, f"summary[{key}] is negative: {summary[key]}"

    def test_chart_data_date_format(self, client: TestClient, auth_headers):
        response = client.get("/reports/disbursements", headers=auth_headers)
        assert response.status_code == 200
        chart_data = response.json()["chart_data"]
        if chart_data:
            for item in chart_data:
                assert re.match(r"^\d{4}-\d{2}-\d{2}$", item["date"]), (
                    f"date '{item['date']}' does not match YYYY-MM-DD format"
                )

    def test_chart_data_amounts_non_negative(self, client: TestClient, auth_headers):
        response = client.get("/reports/disbursements", headers=auth_headers)
        assert response.status_code == 200
        chart_data = response.json()["chart_data"]
        if chart_data:
            for item in chart_data:
                assert item["count"] >= 0, f"count is negative: {item['count']}"
                assert item["total_amount"] >= 0, f"total_amount is negative: {item['total_amount']}"

    def test_group_by_week(self, client: TestClient, auth_headers):
        response = client.get("/reports/disbursements?group_by=week", headers=auth_headers)
        assert response.status_code == 200

    def test_group_by_month(self, client: TestClient, auth_headers):
        response = client.get("/reports/disbursements?group_by=month", headers=auth_headers)
        assert response.status_code == 200

    def test_invalid_group_by_rejected(self, client: TestClient, auth_headers):
        response = client.get("/reports/disbursements?group_by=quarter", headers=auth_headers)
        assert response.status_code == 422

    def test_period_days_param(self, client: TestClient, auth_headers):
        response = client.get("/reports/disbursements?period_days=7", headers=auth_headers)
        assert response.status_code == 200

    def test_requires_auth(self, client: TestClient):
        response = client.get("/reports/disbursements")
        assert response.status_code == 401


class TestReviewPerformance:
    def test_returns_200_with_correct_shape(self, client: TestClient, auth_headers):
        response = client.get("/reports/review-performance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "by_officer" in data
        assert isinstance(data["by_officer"], list)
        assert "override_rate_percent" in data
        assert isinstance(data["override_rate_percent"], (int, float))
        assert "ai_agreement_rate" in data
        assert isinstance(data["ai_agreement_rate"], (int, float))

    def test_rates_in_valid_range(self, client: TestClient, auth_headers):
        response = client.get("/reports/review-performance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["override_rate_percent"] <= 100, (
            f"override_rate_percent out of range: {data['override_rate_percent']}"
        )
        assert 0 <= data["ai_agreement_rate"] <= 100, (
            f"ai_agreement_rate out of range: {data['ai_agreement_rate']}"
        )

    def test_by_officer_fields_present(self, client: TestClient, auth_headers):
        response = client.get("/reports/review-performance", headers=auth_headers)
        assert response.status_code == 200
        by_officer = response.json()["by_officer"]
        if by_officer:
            for item in by_officer:
                for field in ("officer_id", "officer_name", "reviewed_count", "avg_review_time_hours", "approved", "rejected", "overridden"):
                    assert field in item, f"Missing field '{field}' in by_officer entry: {item}"

    def test_by_officer_counts_non_negative(self, client: TestClient, auth_headers):
        response = client.get("/reports/review-performance", headers=auth_headers)
        assert response.status_code == 200
        by_officer = response.json()["by_officer"]
        if by_officer:
            for item in by_officer:
                assert item["reviewed_count"] >= 0, f"reviewed_count is negative: {item['reviewed_count']}"
                assert item["avg_review_time_hours"] >= 0, f"avg_review_time_hours is negative: {item['avg_review_time_hours']}"
                assert item["approved"] >= 0, f"approved is negative: {item['approved']}"
                assert item["rejected"] >= 0, f"rejected is negative: {item['rejected']}"
                assert item["overridden"] >= 0, f"overridden is negative: {item['overridden']}"

    def test_period_days_param(self, client: TestClient, auth_headers):
        response = client.get("/reports/review-performance?period_days=90", headers=auth_headers)
        assert response.status_code == 200

    def test_period_days_zero_rejected(self, client: TestClient, auth_headers):
        response = client.get("/reports/review-performance?period_days=0", headers=auth_headers)
        assert response.status_code == 422

    def test_requires_manager_role(self, client: TestClient, auth_headers):
        response = client.get("/reports/review-performance", headers=auth_headers)
        assert response.status_code == 200

    def test_requires_auth(self, client: TestClient):
        response = client.get("/reports/review-performance")
        assert response.status_code == 401


class TestReviewPerformanceRoleGuard:
    def test_officer_cannot_access_review_performance(self, client: TestClient):
        login_response = client.post(
            "/auth/login",
            json={"email": "officer@bank.com", "password": "changeme"},
        )
        if login_response.status_code != 200:
            pytest.skip("officer user not in seed data")

        token_data = login_response.json()
        token = token_data.get("access_token")
        if not token:
            pytest.skip("officer user not in seed data")

        officer_headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/reports/review-performance", headers=officer_headers)
        assert response.status_code == 403
