"""Pluggable alert delivery abstraction for monitoring snapshots."""

import json
import logging
import os
from typing import Protocol

logger = logging.getLogger(__name__)


class AlertAdapter(Protocol):
    def send(self, alert: dict) -> None: ...


class LogAlertAdapter:
    def send(self, alert: dict) -> None:
        logger.warning("underwriting_monitoring_alert", extra={"alert": alert})


class StdoutAlertAdapter:
    def send(self, alert: dict) -> None:
        print(json.dumps({"monitoring_alert": alert}, default=str))


class WebhookAlertAdapter:
    """Stub adapter for future webhook integration."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def send(self, alert: dict) -> None:
        logger.info(
            "webhook_alert_stub",
            extra={"endpoint": self.endpoint, "alert": alert},
        )


def _build_adapters() -> list[AlertAdapter]:
    mode = os.getenv("MONITORING_ALERT_MODE", "log").strip().lower()
    if mode == "stdout":
        return [StdoutAlertAdapter()]
    if mode == "webhook":
        endpoint = os.getenv("MONITORING_WEBHOOK_URL", "stub://monitoring")
        return [WebhookAlertAdapter(endpoint)]
    return [LogAlertAdapter()]


def dispatch_alerts(alerts: list[dict]) -> None:
    adapters = _build_adapters()
    for alert in alerts:
        for adapter in adapters:
            adapter.send(alert)
