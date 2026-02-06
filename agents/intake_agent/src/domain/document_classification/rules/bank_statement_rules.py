MANDATORY_KEYWORDS = [
    "ACCOUNT NUMBER",
    "STATEMENT PERIOD",
]

STRONG_KEYWORDS = [
    "BEGINNING BALANCE",
    "ENDING BALANCE",
    "DEPOSITS",
    "WITHDRAWALS",
    "DAILY BALANCE",
    "INTEREST EARNED",
]

NEGATIVE_KEYWORDS = [
    "W-2",
    "PAY PERIOD",
    "GROSS PAY",
    "NET PAY",
    "SOCIAL SECURITY",
]


def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0

    t = text.upper()

    if any(n in t for n in NEGATIVE_KEYWORDS):
        return 0.0

    mandatory_hits = sum(1 for k in MANDATORY_KEYWORDS if k in t)
    strong_hits = sum(1 for k in STRONG_KEYWORDS if k in t)

    if mandatory_hits == len(MANDATORY_KEYWORDS) and strong_hits >= 3:
        return 0.95
    if mandatory_hits >= 1 and strong_hits >= 2:
        return 0.85

    return 0.0
