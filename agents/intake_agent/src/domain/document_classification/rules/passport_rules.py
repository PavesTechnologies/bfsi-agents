def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0

    text = text.upper()
    score = 0.0

    if "PASSPORT" in text:
        score += 0.5

    if "UNITED STATES OF AMERICA" in text:
        score += 0.3

    # MRZ hint
    if "P<USA" in text.replace(" ", ""):
        score += 0.3

    return min(score, 1.0)
