import re
from typing import Optional

VOTER_ID_RE = re.compile(r'\b([A-Z]{3}\d{7})\b')
VOTER_ID_KEYWORDS = [
    "election commission", "electoral photo identity", "epic",
    "voter", "elector", "chief electoral officer",
]

# "Name :" / "Elector's Name:" / "Name:" labels on the card
_NAME_LABEL_RE = re.compile(
    r"(?:Elector'?s?\s+Name|Name)\s*[:\-]\s*([A-Za-z\s]{4,60})",
    re.IGNORECASE,
)


def _extract_name(text: str) -> Optional[str]:
    """
    Voter ID (EPIC) cards print the holder's name after a 'Name:' or
    'Elector's Name:' label. Returns None when no label is found so
    cross-validation skips the field rather than raising false mismatches.
    """
    match = _NAME_LABEL_RE.search(text)
    if match:
        return match.group(1).strip()
    return None


def validate_voter_id_ocr(text: str) -> dict:
    text_upper = text.upper()
    epic_match = VOTER_ID_RE.search(text_upper)
    epic_number = epic_match.group(1) if epic_match else None

    has_keywords = any(k in text.lower() for k in VOTER_ID_KEYWORDS)

    confidence = 0.0
    if epic_number:
        confidence += 0.5
    if has_keywords:
        confidence += 0.5

    return {
        "doc_type": "voter_id" if confidence >= 0.5 else "INVALID",
        "valid": epic_number is not None and has_keywords,
        "confidence": round(confidence, 3),
        "epic_number": epic_number,
        "name": _extract_name(text),
    }
