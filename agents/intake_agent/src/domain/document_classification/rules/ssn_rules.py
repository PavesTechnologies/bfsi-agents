import re


def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0

    text = text.upper()
    score = 0.0

    if "SOCIAL SECURITY" in text:
        score += 0.5

    if "SSA" in text:
        score += 0.2

    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
        score += 0.3

    return min(score, 1.0)
