import re
from typing import Optional

PAN_RE = re.compile(r'[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]')
PAN_KEYWORDS = ["income tax", "permanent account number", "govt. of india", "government of india"]
_DOB_RE = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')

_ENTITY_MAP = {
    "A": "Association of Persons",
    "B": "Body of Individuals",
    "C": "Company",
    "F": "Firm",
    "G": "Government",
    "H": "HUF",
    "J": "Artificial Juridical Person",
    "L": "Local Authority",
    "P": "Individual",
    "T": "Trust",
}

# Words on the card that are not the holder's name
_PAN_NAME_SKIP = {
    "INCOME", "TAX", "DEPARTMENT", "GOVT", "OF", "INDIA",
    "PERMANENT", "ACCOUNT", "NUMBER", "SIGNATURE", "YOUR", "NAME", "HERE",
    "FATHER", "GOVERNMENT",
}


def _extract_name(text: str) -> Optional[str]:
    """
    PAN card layout: INCOME TAX DEPARTMENT / GOVT. OF INDIA / <Name> / <Father's Name> / <DOB> / <PAN>.

    Strategy 1 (line-based): walk backward from the DOB line, return the first
    purely-alphabetic multi-word line that's not all stop-words.
    Strategy 2 (token-based fallback): scan tokens before DOB match for consecutive
    alphabetic non-stop-word tokens — handles single-line Textract output.
    """
    # --- Strategy 1: line-based ---
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        dob_idx = None
        for i, line in enumerate(lines):
            if _DOB_RE.search(line):
                dob_idx = i
                break
        if dob_idx is not None and dob_idx >= 1:
            for line in reversed(lines[:dob_idx]):
                words = line.split()
                if len(words) < 2 or len(words) > 5:
                    continue
                if not all(re.match(r'^[A-Za-z]+$', w) for w in words):
                    continue
                if all(w.upper() in _PAN_NAME_SKIP for w in words):
                    continue
                return line

    # --- Strategy 2: token-based (single-line OCR) ---
    dob_match = _DOB_RE.search(text)
    if not dob_match:
        return None

    tokens_before = text[:dob_match.start()].split()
    name_tokens: list[str] = []
    for token in reversed(tokens_before):
        upper = token.upper()
        if upper in _PAN_NAME_SKIP:
            if name_tokens:
                break
            continue
        if not re.match(r'^[A-Za-z]+$', token):
            if name_tokens:
                break
            continue
        name_tokens.insert(0, token)
        if len(name_tokens) >= 4:
            break

    return " ".join(name_tokens) if len(name_tokens) >= 2 else None


def validate_pan_ocr(text: str) -> dict:
    pan_match = PAN_RE.search(text.upper())
    pan_number = pan_match.group() if pan_match else None

    has_keywords = any(k in text.lower() for k in PAN_KEYWORDS)
    format_valid = pan_number is not None

    dob_match = _DOB_RE.search(text)

    confidence = 0.0
    if pan_number:
        confidence += 0.5
    if has_keywords:
        confidence += 0.5

    return {
        "doc_type": "pan_card" if format_valid else "INVALID",
        "valid": format_valid and has_keywords,
        "confidence": round(confidence, 3),
        "pan_number": pan_number,
        "pan_entity_type": _ENTITY_MAP.get(pan_number[3], "Other") if pan_number else None,
        "dob": dob_match.group(1) if dob_match else None,
        "name": _extract_name(text),
    }
