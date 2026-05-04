FORM16_KEYWORDS = [
    "FORM 16",
    "FORM NO. 16",
    "FORM-16",
    "CERTIFICATE OF TAX DEDUCTED AT SOURCE",
    "TDS CERTIFICATE",
    "UNDER SECTION 203",
    "INCOME TAX ACT",
    "ASSESSMENT YEAR",
    "FINANCIAL YEAR",
    "GROSS TOTAL INCOME",
    "TOTAL INCOME",
    "TAN",
    "SALARY PAID",
]


def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0
    text_u = text.upper()
    hits = sum(1 for k in FORM16_KEYWORDS if k in text_u)

    if hits >= 4:
        return 0.95
    if hits == 3:
        return 0.85
    if hits == 2:
        return 0.70
    if hits == 1:
        return 0.40
    return 0.0
