# src/core/logging.py

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime

from src.core.config import get_settings

request_id_ctx: ContextVar[str] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        settings = get_settings()

        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": settings.service_name,
            "env": settings.env,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # 👇 tag the handler so we can detect it
    handler.name = "app-json-handler"

    root = logging.getLogger()
    root.setLevel(get_settings().log_level)

    # ✅ add OUR handler if not already present
    if not any(getattr(h, "name", None) == "app-json-handler" for h in root.handlers):
        root.addHandler(handler)
