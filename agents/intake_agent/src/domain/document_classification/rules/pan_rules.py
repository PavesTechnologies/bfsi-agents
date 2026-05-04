AADHAAR_KEYWORDS = [
    "INCOME TAX",
    "PERMANENT ACCOUNT NUMBER",
    "GOVT. OF INDIA",
    "GOVERNMENT OF INDIA",
    "INCOME TAX DEPARTMENT",
]


def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0
    text_u = text.upper()
    hits = sum(1 for k in AADHAAR_KEYWORDS if k in text_u)

    if hits >= 2:
        return 0.95
    if hits == 1:
        return 0.70
    return 0.0
