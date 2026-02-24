FORM1040_KEYWORDS = [
    "FORM 1040",
    "U.S. INDIVIDUAL INCOME TAX RETURN",
    "INTERNAL REVENUE SERVICE",
    "FILING STATUS",
    "DEPENDENTS",
    "TAXABLE INCOME",
    "TOTAL INCOME",
    "ADJUSTED GROSS INCOME",
    "FEDERAL INCOME TAX WITHHELD",
    "REFUND",
    "AMOUNT YOU OWE",
    "STANDARD DEDUCTION",
    "SIGN HERE",
]


def match(text: str, ocr_blocks=None) -> float:
    """
    Form 1040 classification rules.

    STRONG POSITIVE SIGNALS:
    - IRS tax language
    - Income + tax calculation fields
    - Filing status / dependents section

    Designed to avoid confusion with W2 and Pay Stub.
    """

    if not text:
        return 0.0

    text_u = text.upper()
    hits = sum(1 for k in FORM1040_KEYWORDS if k in text_u)

    # Strong confidence thresholds
    if hits >= 5:
        return 0.92
    if hits == 4:
        return 0.85
    if hits == 3:
        return 0.72
    if hits == 2:
        return 0.6

    return 0.0
