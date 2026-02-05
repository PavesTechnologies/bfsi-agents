def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0

    text = text.upper()
    score = 0.0

    if "FORM W-2" in text or "WAGE AND TAX STATEMENT" in text:
        score += 0.6

    if "BOX 1" in text and "BOX 2" in text:
        score += 0.3

    return min(score, 1.0)
