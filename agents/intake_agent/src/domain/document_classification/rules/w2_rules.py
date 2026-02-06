MANDATORY_KEYWORDS = [
    "W-2",
    "WAGE AND TAX STATEMENT",
]

STRONG_KEYWORDS = [
    "EMPLOYER IDENTIFICATION NUMBER",
    "FEDERAL INCOME TAX WITHHELD",
    "SOCIAL SECURITY WAGES",
    "MEDICARE WAGES",
]

NEGATIVE_KEYWORDS = [
    "PAY PERIOD",
    "NET PAY",
    "ACCOUNT BALANCE",
]


def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0

    t = text.upper()

    if any(n in t for n in NEGATIVE_KEYWORDS):
        return 0.0

    mandatory_hits = sum(1 for k in MANDATORY_KEYWORDS if k in t)
    strong_hits = sum(1 for k in STRONG_KEYWORDS if k in t)

    if mandatory_hits == 2 and strong_hits >= 3:
        return 0.97
    if mandatory_hits >= 1 and strong_hits >= 2:
        return 0.9
    if mandatory_hits >= 1 and strong_hits >= 1:
        return 0.85

    return 0.0
