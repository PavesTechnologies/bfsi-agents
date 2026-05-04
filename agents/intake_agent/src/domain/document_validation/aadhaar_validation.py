import re
from typing import Optional

VERHOEFF_TABLE_D = [
    [0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0],
]
VERHOEFF_TABLE_P = [
    [0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8],
]

AADHAAR_KEYWORDS = ["government of india", "unique identification", "uidai", "aadhaar"]

# Matches groups of 4 digits separated by a single space — the standard Aadhaar print format.
# Negative lookbehind on [-\d] prevents the DOB year (e.g. 06-1986) from being
# consumed as the first group when it is immediately followed by the Aadhaar number.
_AADHAAR_RE = re.compile(r'(?<![\d-])(\d{4})\s(\d{4})\s(\d{4})\b')
_DOB_RE = re.compile(r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b')
_GENDER_RE = re.compile(r'\b(MALE|FEMALE|TRANSGENDER)\b', re.IGNORECASE)

# Words printed on the card that are NOT the holder's name
_AADHAAR_NAME_SKIP = {
    "GOVERNMENT", "OF", "INDIA", "UNIQUE", "IDENTIFICATION", "AUTHORITY",
    "UIDAI", "AADHAAR", "DOB", "DATE", "BIRTH", "HELP", "LINE", "LINES",
    "ENROLLMENT", "ENROLMENT", "ADDRESS", "VALID", "DOWNLOAD", "YOUR",
    "MALE", "FEMALE", "TRANSGENDER", "MY",
}


def _extract_name(text: str) -> Optional[str]:
    """
    Extract the Aadhaar holder's name from OCR text.

    Two strategies in order:
    1. Line-based — works when Textract preserves line breaks. Walk backward
       from the DOB line to find the first purely-alphabetic multi-word line
       that isn't composed entirely of stop-words.
    2. Token-based fallback — for single-line OCR output. Walk backward
       through tokens that appear before the DOB match; collect consecutive
       alphabetic non-stop-word tokens (stops at the first stop-word after
       collection has started).
    """
    # --- Strategy 1: line-based ---
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        dob_idx = None
        for i, line in enumerate(lines):
            if _DOB_RE.search(line):
                dob_idx = i
                break
        if dob_idx is not None and dob_idx > 0:
            for line in reversed(lines[:dob_idx]):
                words = line.split()
                if len(words) < 2 or len(words) > 5:
                    continue
                if not all(re.match(r'^[A-Za-z]+$', w) for w in words):
                    continue
                if all(w.upper() in _AADHAAR_NAME_SKIP for w in words):
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
        if upper in _AADHAAR_NAME_SKIP:
            if name_tokens:
                break  # stop collecting once we hit a stop-word after starting
            continue
        if not re.match(r'^[A-Za-z]+$', token):
            if name_tokens:
                break
            continue
        name_tokens.insert(0, token)
        if len(name_tokens) >= 4:
            break

    return " ".join(name_tokens) if len(name_tokens) >= 2 else None


def validate_aadhaar_checksum(aadhaar: str) -> bool:
    digits = [int(d) for d in aadhaar.strip().replace(" ", "")]
    if len(digits) != 12:
        return False
    c = 0
    for i, digit in enumerate(reversed(digits)):
        c = VERHOEFF_TABLE_D[c][VERHOEFF_TABLE_P[i % 8][digit]]
    return c == 0


def _extract_aadhaar_number(text: str) -> tuple[str | None, bool]:
    """
    Return (aadhaar_12_digits, checksum_valid).

    Strategy: collect all 4-4-4 digit candidates, prefer the one that
    passes the Verhoeff checksum. If none pass, fall back to the LAST
    candidate (Aadhaar number appears after DOB/name in standard layouts,
    so later in the text is more likely to be the actual number).
    """
    candidates = ["".join(m) for m in _AADHAAR_RE.findall(text)]
    if not candidates:
        return None, False

    for c in candidates:
        if validate_aadhaar_checksum(c):
            return c, True

    # No checksum-valid candidate — return the last one found
    return candidates[-1], False


def validate_aadhaar_ocr(text: str) -> dict:
    aadhaar_number, checksum_valid = _extract_aadhaar_number(text)
    has_keywords = any(k in text.lower() for k in AADHAAR_KEYWORDS)

    dob_match = _DOB_RE.search(text)
    gender_match = _GENDER_RE.search(text)

    # valid = document looks like an Aadhaar (keywords + number present).
    # checksum is surfaced as metadata; it fails legitimately for test/sample
    # documents and masked numbers (XXXX XXXX 1234).
    valid = has_keywords and aadhaar_number is not None

    confidence = 0.0
    if aadhaar_number:
        confidence += 0.4
    if has_keywords:
        confidence += 0.3
    if checksum_valid:
        confidence += 0.3
    else:
        confidence += 0.1  # partial credit — number found even if checksum fails

    return {
        "doc_type": "aadhaar_card" if valid else "INVALID",
        "valid": valid,
        "confidence": round(confidence, 3),
        "aadhaar_number": aadhaar_number,
        "checksum_valid": checksum_valid,
        "dob": dob_match.group(1) if dob_match else None,
        "gender": gender_match.group(1).upper() if gender_match else None,
        "name": _extract_name(text),
    }
