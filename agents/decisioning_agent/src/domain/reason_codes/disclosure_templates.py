"""Disclosure-safe templates for adverse-action and reviewer-facing messaging."""

from src.domain.reason_codes.reason_registry import REGULATORY_REASON_MAPPING


DISCLOSURE_TEMPLATES = {
    reason_key: {
        "notice_text": reason["official_text"],
        "reviewer_text": f"{reason['official_text']} ({reason['trigger_logic']})",
        "internal_text": f"Triggered {reason_key} because {reason['trigger_logic']}.",
    }
    for reason_key, reason in REGULATORY_REASON_MAPPING.items()
}


def render_notice(reason_keys: list[str]) -> str:
    return "; ".join(DISCLOSURE_TEMPLATES[key]["notice_text"] for key in reason_keys)
