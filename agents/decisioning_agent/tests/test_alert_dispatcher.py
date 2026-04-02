import os

from src.services.monitoring.alert_dispatcher import dispatch_alerts


def test_dispatch_alerts_supports_stdout_mode(capsys):
    os.environ["MONITORING_ALERT_MODE"] = "stdout"
    try:
        dispatch_alerts([{"alert_type": "APPROVAL_RATE_SHIFT", "severity": "HIGH"}])
        captured = capsys.readouterr()
        assert "APPROVAL_RATE_SHIFT" in captured.out
    finally:
        os.environ.pop("MONITORING_ALERT_MODE", None)


def test_dispatch_alerts_supports_webhook_stub_mode():
    os.environ["MONITORING_ALERT_MODE"] = "webhook"
    os.environ["MONITORING_WEBHOOK_URL"] = "stub://example"
    try:
        dispatch_alerts([{"alert_type": "DISPARATE_IMPACT_BREACH", "severity": "HIGH"}])
    finally:
        os.environ.pop("MONITORING_ALERT_MODE", None)
        os.environ.pop("MONITORING_WEBHOOK_URL", None)
