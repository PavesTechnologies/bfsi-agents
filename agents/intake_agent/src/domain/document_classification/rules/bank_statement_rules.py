def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0

    text = text.upper()
    score = 0.0

    if "BANK STATEMENT" in text:
        score += 0.4

    if "BEGINNING BALANCE" in text:
        score += 0.3

    if "ENDING BALANCE" in text:
        score += 0.3

    if "ACCOUNT NUMBER" in text:
        score += 0.2

    return min(score, 1.0)
