import re
import pytest
from fastapi.testclient import TestClient


class TestDashboard:
    def test_returns_200_with_correct_shape(self, client: TestClient, auth_headers):
        response = client.get("/reports/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        expected_fields = [
            "total_applications",
            "pending_review",
            "in_review",
            "approved_today",
            "rejected_today",
            "total_disbursed_amount",
            "avg_risk_score",
            "approval_rate_percent",
            "avg_loan_amount",
            "avg_processing_time_hours",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], (int, float)), f"Field {field} is not a number"

    def test_all_fields_are_non_negative(self, client: TestClient, auth_headers):
        response = client.get("/reports/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        expected_fields = [
            "total_applications",
            "pending_review",
            "in_review",
            "approved_today",
            "rejected_today",
            "total_disbursed_amount",
            "avg_risk_score",
            "approval_rate_percent",
            "avg_loan_amount",
            "avg_processing_time_hours",
        ]
        for field in expected_fields:
            assert data[field] >= 0, f"Field {field} is negative: {data[field]}"

    def test_period_days_param(self, client: TestClient, auth_headers):
        response = client.get("/reports/dashboard?period_days=7", headers=auth_headers)
        assert response.status_code == 200

    def test_period_days_zero_rejected(self, client: TestClient, auth_headers):
        response = client.get("/reports/dashboard?period_days=0", headers=auth_headers)
        assert response.status_code == 422

    def test_requires_auth(self, client: TestClient):
        response = client.get("/reports/dashboard")
        assert response.status_code == 401


class TestApplicationsReport:
    def test_returns_200_with_correct_shape(self, client: TestClient, auth_headers):
        response = client.get("/reports/applications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "chart_data" in data
        assert isinstance(data["chart_data"], list)
        assert "summary" in data
        summary_keys = [
            "total",
            "approved",
            "declined",
            "counter_offer",
            "pending_human_review",
            "human_rejected",
        ]
        for key in summary_keys:
            assert key in data["summary"], f"Missing summary key: {key}"

    def test_summary_fields_are_non_negative(self, client: TestClient, auth_headers):
        response = client.get("/reports/applications", headers=auth_headers)
        assert response.status_code == 200
        summary = response.json()["summary"]
        for key, value in summary.items():
            assert value >= 0, f"Summary field {key} is negative: {value}"

    def test_chart_data_date_format(self, client: TestClient, auth_headers):
        response = client.get("/reports/applications", headers=auth_headers)
        assert response.status_code == 200
        chart_data = response.json()["chart_data"]
        if chart_data:
            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
            for item in chart_data:
                assert "date" in item, "chart_data item missing 'date' field"
                assert date_pattern.match(item["date"]), (
                    f"Date '{item['date']}' does not match YYYY-MM-DD format"
                )

    def test_group_by_week(self, client: TestClient, auth_headers):
        response = client.get("/reports/applications?group_by=week", headers=auth_headers)
        assert response.status_code == 200

    def test_group_by_month(self, client: TestClient, auth_headers):
        response = client.get("/reports/applications?group_by=month", headers=auth_headers)
        assert response.status_code == 200

    def test_invalid_group_by_rejected(self, client: TestClient, auth_headers):
        response = client.get("/reports/applications?group_by=hour", headers=auth_headers)
        assert response.status_code == 422

    def test_requires_auth(self, client: TestClient):
        response = client.get("/reports/applications")
        assert response.status_code == 401


class TestRiskDistribution:
    EXPECTED_BUCKETS = [
        "300-400",
        "400-500",
        "500-600",
        "600-650",
        "650-700",
        "700-750",
        "750-800",
        "800-850",
        "850-900",
        "900+",
    ]

    def test_returns_200_with_correct_shape(self, client: TestClient, auth_headers):
        response = client.get("/reports/risk-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "by_tier" in data
        assert isinstance(data["by_tier"], list)
        assert "score_histogram" in data
        assert isinstance(data["score_histogram"], list)

    def test_score_histogram_has_10_fixed_buckets(self, client: TestClient, auth_headers):
        response = client.get("/reports/risk-distribution", headers=auth_headers)
        assert response.status_code == 200
        score_histogram = response.json()["score_histogram"]
        assert len(score_histogram) == 10, (
            f"Expected 10 histogram buckets, got {len(score_histogram)}"
        )
        bucket_labels = [item["bucket"] for item in score_histogram]
        assert bucket_labels == self.EXPECTED_BUCKETS, (
            f"Bucket labels mismatch. Got: {bucket_labels}"
        )

    def test_score_histogram_counts_non_negative(self, client: TestClient, auth_headers):
        response = client.get("/reports/risk-distribution", headers=auth_headers)
        assert response.status_code == 200
        score_histogram = response.json()["score_histogram"]
        for item in score_histogram:
            assert item["count"] >= 0, (
                f"Bucket '{item['bucket']}' has negative count: {item['count']}"
            )

    def test_by_tier_fields_present(self, client: TestClient, auth_headers):
        response = client.get("/reports/risk-distribution", headers=auth_headers)
        assert response.status_code == 200
        by_tier = response.json()["by_tier"]
        if by_tier:
            required_fields = ["tier", "count", "total_amount", "avg_rate", "approval_rate"]
            for item in by_tier:
                for field in required_fields:
                    assert field in item, (
                        f"Tier item missing field '{field}': {item}"
                    )

    def test_approval_rate_in_range(self, client: TestClient, auth_headers):
        response = client.get("/reports/risk-distribution", headers=auth_headers)
        assert response.status_code == 200
        by_tier = response.json()["by_tier"]
        if by_tier:
            for item in by_tier:
                assert 0 <= item["approval_rate"] <= 100, (
                    f"approval_rate out of range for tier '{item['tier']}': {item['approval_rate']}"
                )

    def test_period_days_param(self, client: TestClient, auth_headers):
        response = client.get("/reports/risk-distribution?period_days=90", headers=auth_headers)
        assert response.status_code == 200

    def test_requires_auth(self, client: TestClient):
        response = client.get("/reports/risk-distribution")
        assert response.status_code == 401
