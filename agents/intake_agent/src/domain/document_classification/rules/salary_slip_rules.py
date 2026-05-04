SALARY_SLIP_KEYWORDS = [
    "SALARY SLIP",
    "PAY SLIP",
    "PAYSLIP",
    "SALARY STATEMENT",
    "BASIC SALARY",
    "BASIC PAY",
    "GROSS SALARY",
    "GROSS PAY",
    "NET SALARY",
    "NET PAY",
    "HRA",
    "HOUSE RENT ALLOWANCE",
    "PROVIDENT FUND",
    "EMPLOYEE ID",
    "EMPLOYEE CODE",
    "TDS",
]


def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0
    text_u = text.upper()
    hits = sum(1 for k in SALARY_SLIP_KEYWORDS if k in text_u)

    if hits >= 4:
        return 0.95
    if hits == 3:
        return 0.85
    if hits == 2:
        return 0.70
    if hits == 1:
        return 0.40
    return 0.0
