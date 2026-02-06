"""
Passport document keyword validation rules.

Design goals:
- Extremely low false positives
- OCR-noise tolerant
- Complementary to MRZ validation (not a replacement)
- Deterministic (no ML / vision dependency)
"""

# -----------------------------
# Mandatory indicators
# -----------------------------
# At least ONE must exist
MANDATORY_KEYWORDS = [
    "PASSPORT",
    "REPUBLIC OF",
    "UNITED STATES OF AMERICA",
]

# -----------------------------
# Strong semantic indicators
# -----------------------------
STRONG_KEYWORDS = [
    "NATIONALITY",
    "DATE OF BIRTH",
    "PLACE OF BIRTH",
    "DATE OF ISSUE",
    "DATE OF EXPIRY",
    "AUTHORITY",
    "PASSPORT NO",
    "PASSPORT NUMBER",
]

# -----------------------------
# Machine Readable Zone signals
# -----------------------------
# These patterns almost never appear outside passports
MRZ_MARKERS = [
    "<<",
    "P<",
]

# -----------------------------
# Hard negative indicators
# -----------------------------
NEGATIVE_KEYWORDS = [
    # Driver License
    "DRIVER LICENSE",
    "DL NO",
    "LICENSE NUMBER",

    # Income documents
    "PAY PERIOD",
    "NET PAY",
    "GROSS PAY",
    "W-2",
    "WAGE AND TAX STATEMENT",

    # Financial documents
    "ACCOUNT NUMBER",
    "STATEMENT PERIOD",
    "BEGINNING BALANCE",

    # SSN
    "SOCIAL SECURITY",
]


def match(text: str, ocr_blocks=None) -> float:
    """
    Returns confidence score for passport document.

    Confidence levels:
    - 0.97 → definitive passport
    - 0.90 → very strong passport
    - 0.85 → acceptable passport
    - 0.0  → reject
    """

    if not text:
        return 0.0

    t = text.upper()

    # -----------------------------
    # Hard rejection
    # -----------------------------
    if any(neg in t for neg in NEGATIVE_KEYWORDS):
        return 0.0

    mandatory_hits = sum(1 for k in MANDATORY_KEYWORDS if k in t)
    strong_hits = sum(1 for k in STRONG_KEYWORDS if k in t)
    mrz_hits = sum(1 for k in MRZ_MARKERS if k in t)

    # -----------------------------
    # Confidence scoring
    # -----------------------------

    # Gold standard:
    # - Passport keyword
    # - MRZ present
    # - Multiple semantic fields
    if mandatory_hits >= 1 and mrz_hits >= 1 and strong_hits >= 3:
        return 0.97

    # Very strong:
    if mandatory_hits >= 1 and strong_hits >= 3:
        return 0.90

    # Minimum acceptable:
    if mandatory_hits >= 1 and strong_hits >= 2:
        return 0.85

    return 0.0
