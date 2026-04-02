import os
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")

from src.repositories.underwriting_repository import UnderwritingRepository
from src.services.fairness.disparate_impact import compute_disparate_impact
from src.services.fairness.drift import compute_population_stability_index
from src.services.fairness.reason_code_analysis import summarize_reason_code_distribution
from src.services.monitoring.alerts import evaluate_release_alerts
from src.services.monitoring.decision_metrics import build_decision_telemetry
from src.services.monitoring.monitoring_report import build_monitoring_snapshot
from src.services.validation.release_report import build_release_report


def test_build_decision_telemetry_normalizes_monitoring_fields():
    telemetry = build_decision_telemetry(
        final_decision={
            "application_id": "APP-100",
            "decision": "DECLINE",
            "risk_tier": "F",
            "risk_score": 18.4,
            "policy_version": "v2.0",
            "primary_reason_key": "DTI_HIGH",
            "secondary_reason_key": "EXPOSURE_HIGH",
            "audit_summary": {
                "model_version": "openai/gpt-oss-120b",
                "prompt_version": "deterministic-underwriting-v1",
                "triggered_reason_keys": ["DTI_HIGH", "EXPOSURE_HIGH"],
            },
        },
        evaluation_attributes={"segment": "segment_a"},
    )

    assert telemetry["application_id"] == "APP-100"
    assert telemetry["decision_group"] == "negative"
    assert telemetry["is_approved"] is False
    assert telemetry["triggered_reason_keys"] == ["DTI_HIGH", "EXPOSURE_HIGH"]
    assert telemetry["evaluation_attributes"]["segment"] == "segment_a"


def test_underwriting_repository_build_monitoring_payload_projects_record():
    repo = UnderwritingRepository(SimpleNamespace())
    record = SimpleNamespace(
        application_id="APP-200",
        decision="APPROVE",
        risk_tier="B",
        risk_score=72.1,
        policy_version="v2.0",
        model_version="openai/gpt-oss-120b",
        prompt_version="deterministic-underwriting-v1",
        primary_reason_key=None,
        secondary_reason_key=None,
        approved_amount=Decimal("15000.00"),
        counter_offer_data=None,
        raw_decision_payload={},
        audit_narrative={"triggered_reason_keys": []},
    )

    telemetry = repo.build_monitoring_payload(
        record,
        evaluation_attributes={"state_group": "urban"},
    )

    assert telemetry["is_approved"] is True
    assert telemetry["approved_amount"] == 15000.0
    assert telemetry["evaluation_attributes"]["state_group"] == "urban"


def test_compute_disparate_impact_flags_below_four_fifths_rule():
    records = [
        {"is_approved": True, "evaluation_attributes": {"segment": "A"}},
        {"is_approved": True, "evaluation_attributes": {"segment": "A"}},
        {"is_approved": False, "evaluation_attributes": {"segment": "A"}},
        {"is_approved": False, "evaluation_attributes": {"segment": "B"}},
        {"is_approved": False, "evaluation_attributes": {"segment": "B"}},
        {"is_approved": True, "evaluation_attributes": {"segment": "B"}},
        {"is_approved": False, "evaluation_attributes": {"segment": "B"}},
    ]

    report = compute_disparate_impact(records, segment_key="segment")

    assert report["reference_segment"] == "A"
    assert report["segments"]["A"]["positive_rate"] > report["segments"]["B"]["positive_rate"]
    assert report["segments"]["B"]["passes_four_fifths_rule"] is False


def test_reason_code_distribution_and_psi_capture_monitoring_shifts():
    records = [
        {
            "triggered_reason_keys": ["DTI_HIGH", "EXPOSURE_HIGH"],
            "evaluation_attributes": {"segment": "A"},
        },
        {
            "triggered_reason_keys": ["DTI_HIGH"],
            "evaluation_attributes": {"segment": "A"},
        },
        {
            "triggered_reason_keys": ["BANKRUPTCY_RECENT"],
            "evaluation_attributes": {"segment": "B"},
        },
    ]

    distribution = summarize_reason_code_distribution(records, segment_key="segment")
    psi = compute_population_stability_index(
        baseline_values=["APPROVE", "APPROVE", "DECLINE", "DECLINE"],
        current_values=["DECLINE", "DECLINE", "DECLINE", "APPROVE"],
    )

    assert distribution["segments"]["A"]["reason_counts"]["DTI_HIGH"] == 2
    assert distribution["segments"]["B"]["reason_rates"]["BANKRUPTCY_RECENT"] == 1.0
    assert psi["psi"] > 0
    assert psi["severity"] in {"LOW", "MODERATE", "HIGH"}


def test_release_report_combines_rates_drift_and_reason_disparities():
    baseline = [
        build_decision_telemetry(
            final_decision={
                "application_id": "APP-1",
                "decision": "APPROVE",
                "risk_tier": "B",
                "audit_summary": {"triggered_reason_keys": []},
            },
            evaluation_attributes={"segment": "A"},
        ),
        build_decision_telemetry(
            final_decision={
                "application_id": "APP-2",
                "decision": "DECLINE",
                "risk_tier": "F",
                "primary_reason_key": "DTI_HIGH",
                "secondary_reason_key": "EXPOSURE_HIGH",
                "audit_summary": {"triggered_reason_keys": ["DTI_HIGH", "EXPOSURE_HIGH"]},
            },
            evaluation_attributes={"segment": "B"},
        ),
    ]
    current = [
        build_decision_telemetry(
            final_decision={
                "application_id": "APP-3",
                "decision": "DECLINE",
                "risk_tier": "F",
                "primary_reason_key": "DTI_HIGH",
                "secondary_reason_key": "EXPOSURE_HIGH",
                "audit_summary": {"triggered_reason_keys": ["DTI_HIGH", "EXPOSURE_HIGH"]},
            },
            evaluation_attributes={"segment": "A"},
        ),
        build_decision_telemetry(
            final_decision={
                "application_id": "APP-4",
                "decision": "DECLINE",
                "risk_tier": "F",
                "primary_reason_key": "BANKRUPTCY_RECENT",
                "secondary_reason_key": "DTI_HIGH",
                "audit_summary": {"triggered_reason_keys": ["BANKRUPTCY_RECENT", "DTI_HIGH"]},
            },
            evaluation_attributes={"segment": "B"},
        ),
    ]

    report = build_release_report(
        baseline_records=baseline,
        current_records=current,
        segment_key="segment",
    )

    assert report["baseline_sample_size"] == 2
    assert report["current_sample_size"] == 2
    assert report["approval_rate_change"] < 0
    assert "segments" in report["current_disparate_impact"]
    assert "segments" in report["current_reason_distribution"]
    assert report["decision_drift"]["psi"] >= 0


def test_evaluate_release_alerts_detects_major_monitoring_breaches():
    report = {
        "approval_rate_change": -0.25,
        "decision_drift": {"psi": 0.31},
        "risk_tier_drift": {"psi": 0.29},
        "current_disparate_impact": {
            "segments": {
                "B": {"disparate_impact_ratio": 0.62},
            }
        },
        "current_reason_distribution": {
            "segments": {
                "B": {
                    "reason_rates": {
                        "BANKRUPTCY_RECENT": 0.82,
                    }
                }
            }
        },
    }

    alerts = evaluate_release_alerts(report)

    alert_types = {alert["alert_type"] for alert in alerts}
    assert "APPROVAL_RATE_SHIFT" in alert_types
    assert "DECISION_DRIFT" in alert_types
    assert "RISK_TIER_DRIFT" in alert_types
    assert "DISPARATE_IMPACT_BREACH" in alert_types
    assert "REASON_CODE_CONCENTRATION" in alert_types


def test_build_monitoring_snapshot_packages_report_and_alerts():
    baseline = [
        build_decision_telemetry(
            final_decision={
                "application_id": "APP-10",
                "decision": "APPROVE",
                "risk_tier": "B",
                "audit_summary": {"triggered_reason_keys": []},
            },
            evaluation_attributes={"segment": "A"},
        ),
        build_decision_telemetry(
            final_decision={
                "application_id": "APP-11",
                "decision": "APPROVE",
                "risk_tier": "B",
                "audit_summary": {"triggered_reason_keys": []},
            },
            evaluation_attributes={"segment": "B"},
        ),
    ]
    current = [
        build_decision_telemetry(
            final_decision={
                "application_id": "APP-12",
                "decision": "DECLINE",
                "risk_tier": "F",
                "primary_reason_key": "BANKRUPTCY_RECENT",
                "secondary_reason_key": "DTI_HIGH",
                "audit_summary": {"triggered_reason_keys": ["BANKRUPTCY_RECENT", "DTI_HIGH"]},
            },
            evaluation_attributes={"segment": "B"},
        ),
        build_decision_telemetry(
            final_decision={
                "application_id": "APP-13",
                "decision": "DECLINE",
                "risk_tier": "F",
                "primary_reason_key": "BANKRUPTCY_RECENT",
                "secondary_reason_key": "EXPOSURE_HIGH",
                "audit_summary": {"triggered_reason_keys": ["BANKRUPTCY_RECENT", "EXPOSURE_HIGH"]},
            },
            evaluation_attributes={"segment": "B"},
        ),
    ]

    snapshot = build_monitoring_snapshot(
        baseline_records=baseline,
        current_records=current,
        segment_key="segment",
    )

    assert snapshot["segment_key"] == "segment"
    assert snapshot["alert_count"] >= 1
    assert "report" in snapshot
    assert "alerts" in snapshot
