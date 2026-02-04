import re
from .ocr_text_extraction import ocr_text_extraction_from_image_bytes


# -------------------------------
# Passport Signal Checks
# -------------------------------

def has_passport_number(text):
    """
    US passport numbers are typically 9 characters (alphanumeric)
    """
    return bool(re.search(r"^[A-Z][0-9]{8}$", text))

def passport_keyword_score(text):
    keywords = [
        "passport",
        "united states of america",
        "usa",
        "u.s. passport",
        "issued on",
        "expires on"
    ]

    text = text.lower()

    matched_keywords = [k for k in keywords if k in text]
    match_count = len(matched_keywords)

    # normalized score between 0.0 and 1.0
    score = match_count*0.17
    return score, matched_keywords


def calculate_confidence(text):
    score = 0.0

    # Passport number signal
    if has_passport_number(text):
        print("Passport number format detected.")
        score += 0.6
    else:
        print("No valid passport number format detected.")

    # Keyword signal (scaled)
    keyword_score, matched = passport_keyword_score(text)
    score += keyword_score

    return min(score, 1.0)



def validate_passport(text):
    keyword_score, matched_keywords = passport_keyword_score(text)
    has_number = has_passport_number(text)

    confidence = calculate_confidence(text)

    is_valid = (
        has_number and
        keyword_score >= 0.7 and  # at least half the keywords
        confidence >= 0.8
    )

    return {
        "doc_type": "PASSPORT" if is_valid else "INVALID",
        "confidence": round(confidence, 3),
        "matched_keywords": matched_keywords,
        "valid": is_valid
    }


# -------------------------------
# OCR + Validation Pipeline
# -------------------------------

def passport_validation(processed_image_bytes):
    """
    End-to-end USA passport validation
    """
    print("Starting USA Passport Validation Pipeline...")

    # OCR (from processed image only)
    ocr_text = ocr_text_extraction_from_image_bytes(processed_image_bytes)

    # Validate passport
    result = validate_passport(ocr_text)

    print("\n===== FINAL RESULT =====")
    print(result)
    print("========================")

    return result
