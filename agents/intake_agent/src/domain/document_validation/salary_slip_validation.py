import re

SALARY_SLIP_KEYWORDS = [
    "salary slip", "pay slip", "payslip", "salary statement",
    "basic salary", "basic pay", "gross salary", "gross pay",
    "net salary", "net pay", "net amount",
    "hra", "house rent allowance",
    "pf", "provident fund", "epf",
    "tds", "tax deducted",
    "deductions", "earnings",
    "employee id", "employee code", "emp id",
    "month", "month of",
]

_AMOUNT_RE = re.compile(r'(?:rs\.?|inr|₹)\s*[\d,]+(?:\.\d{2})?', re.IGNORECASE)
_MONTH_RE = re.compile(
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december'
    r'|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b',
    re.IGNORECASE,
)


def validate_salary_slip_ocr(text: str) -> dict:
    text_lower = text.lower()
    hits = sum(1 for k in SALARY_SLIP_KEYWORDS if k in text_lower)

    amounts = _AMOUNT_RE.findall(text)
    month_match = _MONTH_RE.search(text)

    if hits >= 4:
        confidence = 0.95
    elif hits == 3:
        confidence = 0.85
    elif hits == 2:
        confidence = 0.70
    elif hits == 1:
        confidence = 0.40
    else:
        confidence = 0.0

    valid = confidence >= 0.70

    return {
        "doc_type": "salary_slip" if valid else "INVALID",
        "valid": valid,
        "confidence": round(confidence, 3),
        "keyword_hits": hits,
        "amounts_found": amounts[:5],
        "pay_month": month_match.group(0).capitalize() if month_match else None,
    }
