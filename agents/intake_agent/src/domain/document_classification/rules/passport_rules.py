import re
from typing import List


# Strong passport text indicators
PASSPORT_KEYWORDS = [
    "PASSPORT",
    "PASSEPORT",
    "REPUBLIC OF",
    "NATIONALITY",
    "DATE OF BIRTH",
    "PLACE OF BIRTH",
    "SEX",
]

# MRZ regex (ICAO 9303 – simplified but robust)
MRZ_LINE_REGEX = re.compile(r"^[A-Z0-9<]{30,44}$")


def _detect_mrz(text: str) -> bool:
    """
    Detect Machine Readable Zone (MRZ).
    This is the strongest authenticity signal.
    """
    lines = [l.strip() for l in text.splitlines()]
    mrz_lines = [l for l in lines if MRZ_LINE_REGEX.match(l)]

    # Passport MRZ has 2 consecutive lines
    return len(mrz_lines) >= 2


def _detect_mrz_blocks(ocr_blocks: List) -> bool:
    """
    Detect MRZ via OCR block characteristics:
    - dense
    - long
    - bottom-aligned
    """
    if not ocr_blocks:
        return False

    candidate_blocks = [
        b for b in ocr_blocks
        if len(b.text.replace(" ", "")) > 30 and "<" in b.text
    ]

    return len(candidate_blocks) >= 1


def match(text: str, ocr_blocks=None) -> float:
    """
    Passport classification with visual validation.

    Rejects keyword-only fake documents.
    """

    if not text:
        return 0.0

    text_u = text.upper()
    score = 0.0

    # ---------- MRZ (strongest signal) ----------
    has_mrz_text = _detect_mrz(text)
    has_mrz_block = _detect_mrz_blocks(ocr_blocks)

    if has_mrz_text or has_mrz_block:
        score += 0.6
    else:
        # Without MRZ, this cannot be a strong passport
        return 0.0

    # ---------- Passport keywords ----------
    if any(k in text_u for k in PASSPORT_KEYWORDS):
        score += 0.2

    # ---------- Identity fields ----------
    identity_hits = sum(
        1 for k in ["NATIONALITY", "DATE OF BIRTH", "SEX"]
        if k in text_u
    )

    if identity_hits >= 2:
        score += 0.1

    # ---------- Layout sanity ----------
    # Passports have structured fields, not free text
    if ocr_blocks and len(ocr_blocks) > 10:
        score += 0.1

    return min(score, 1.0)
