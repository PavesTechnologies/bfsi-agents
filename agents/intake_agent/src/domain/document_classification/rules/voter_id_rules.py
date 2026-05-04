VOTER_ID_KEYWORDS = [
    "ELECTION COMMISSION",
    "ELECTORAL PHOTO IDENTITY",
    "EPIC",
    "VOTER",
    "ELECTOR",
    "CHIEF ELECTORAL OFFICER",
]


def match(text: str, ocr_blocks=None) -> float:
    if not text:
        return 0.0
    text_u = text.upper()
    hits = sum(1 for k in VOTER_ID_KEYWORDS if k in text_u)

    if hits >= 3:
        return 0.95
    if hits == 2:
        return 0.85
    if hits == 1:
        return 0.60
    return 0.0
