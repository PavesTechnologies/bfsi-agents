import re

FORM16_KEYWORDS = [
    "form 16", "form no. 16", "form-16",
    "certificate of tax deducted at source",
    "tds certificate",
    "under section 203",
    "income tax act",
    "assessment year",
    "financial year",
    "gross total income",
    "total income",
    "tax on total income",
    "employer",
    "tan",
    "pan of deductee",
    "salary paid",
]

_AY_RE = re.compile(r'\b(20\d{2}-\d{2,4})\b')
_PAN_RE = re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b')
_TAN_RE = re.compile(r'\b[A-Z]{4}\d{5}[A-Z]\b')


def validate_form16_ocr(text: str) -> dict:
    text_lower = text.lower()
    hits = sum(1 for k in FORM16_KEYWORDS if k in text_lower)

    ay_match = _AY_RE.search(text)
    pan_match = _PAN_RE.search(text.upper())
    tan_match = _TAN_RE.search(text.upper())

    if hits >= 4:
        confidence = 0.95
    elif hits == 3:
        confidence = 0.85
    elif hits == 2:
        confidence = 0.70
    elif hits == 1:
        confidence = 0.40
    else:
        confidence = 0.0

    # Boost if structural fields (AY, PAN, TAN) are all present
    if ay_match and pan_match and tan_match:
        confidence = min(confidence + 0.05, 1.0)

    valid = confidence >= 0.70

    return {
        "doc_type": "form_16" if valid else "INVALID",
        "valid": valid,
        "confidence": round(confidence, 3),
        "keyword_hits": hits,
        "assessment_year": ay_match.group(1) if ay_match else None,
        "pan_number": pan_match.group(0) if pan_match else None,
        "tan_number": tan_match.group(0) if tan_match else None,
    }
