import json
import logging
from datetime import datetime


class PIIMaskingFilter(logging.Filter):
    def filter(self, record):
        # Mask SSN: Only show last 4 digits
        if hasattr(record, "ssn") and record.ssn:
            record.ssn = f"***-**-{record.ssn[-4:]}"

        # Prevent raw images or base64 from entering logs
        if hasattr(record, "image_data"):
            record.image_data = "<REDACTED_IMAGE_DATA>"

        return True


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "request_id": getattr(record, "request_id", "N/A"),
            "applicant_id": getattr(record, "applicant_id", "N/A"),
        }
        # Add extra context if provided
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create handler
    handler = logging.StreamHandler()

    # Apply Masking Filter
    handler.addFilter(PIIMaskingFilter())

    # Apply JSON Formatter
    handler.setFormatter(JSONFormatter())

    logger.addHandler(handler)
