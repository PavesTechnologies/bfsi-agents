"""Policy-level regulatory reason definitions."""

from src.domain.reason_codes.reason_registry import REGULATORY_REASON_MAPPING


def load_reason_mapping() -> dict:
    return REGULATORY_REASON_MAPPING
