PAYSTUB_KEYWORDS = [
    "PAY BEGIN DATE",
    "PAY END DATE",
    "HOURS AND EARNINGS",
    "NET PAY",
    "GROSS PAY",
    "BEFORE-TAX DEDUCTIONS",
    "AFTER-TAX DEDUCTIONS",
    "YTD",
    "EARNINGS",
    "DEDUCTIONS",
]


def match(text: str, ocr_blocks=None) -> float:
    """
    Pay Stub classification rules.

    STRONG POSITIVE SIGNALS:
    - Financial payroll language
    - Earnings + deductions structure

    2–3 hits should dominate all ID-like documents.
    """

    if not text:
        return 0.0

    text_u = text.upper()
    hits = sum(1 for k in PAYSTUB_KEYWORDS if k in text_u)

    if hits >= 4:
        return 0.9
    if hits == 3:
        return 0.8
    if hits == 2:
        return 0.65

    return 0.0
