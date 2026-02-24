from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


def to_json_safe(value):
    """Recursively convert Python objects into JSON serializable primitives"""

    if isinstance(value, dict):
        return {k: to_json_safe(v) for k, v in value.items()}

    if isinstance(value, list):
        return [to_json_safe(v) for v in value]

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime | date)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    return value
