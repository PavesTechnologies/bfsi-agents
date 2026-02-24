import re

# from .ocr_text_extraction import ocr_text_extraction_from_image_bytes
from .aws_text_extraction import AWSOCR


def has_ssn_number(text):
    """Check SSN number format"""
    return bool(re.search(r"\b\d{3}-\d{2}-\d{4}\b", text))


def has_ssn_keywords(text):
    """Check SSN-related keywords"""
    keywords = ["social security", "ssa", "social security administration", "signature"]

    text = text.lower()

    return any(k in text for k in keywords)


def calculate_confidence(text):
    """Simple confidence scoring"""

    score = 0.0

    if has_ssn_number(text):
        score += 0.6

    if has_ssn_keywords(text):
        score += 0.4

    return min(score, 1.0)


def extract_ssn(text):
    """Extract SSN number from text"""
    match = re.search(r"\b\d{3}-\d{2}-\d{4}\b", text)
    return match.group() if match else None


def validate_ssn(text):
    has_number = has_ssn_number(text)
    has_keywords = has_ssn_keywords(text)

    confidence = calculate_confidence(text)

    ssn_number = extract_ssn(text)

    is_valid = has_number and has_keywords and confidence >= 0.8

    return {
        "doc_type": "SSN" if is_valid else "INVALID",
        "confidence": round(confidence, 3),
        "ssn_number": ssn_number,
        "valid": is_valid,
    }


# -------------------------------
# OCR + Validation Pipeline
# -------------------------------


def ssn_card_validation(file, document_type, application_id):
    # -------------------------------
    # OCR + Validation Pipeline
    # -------------------------------

    SSN_ocr = AWSOCR()

    print("Starting SSN Card Validation Pipeline...")
    ocr_text = SSN_ocr.process_file(file, document_type, application_id)

    text = " ".join(ocr_text["lines"]) if ocr_text["status"] == "success" else ""

    # Validate SSN
    result = validate_ssn(text)
    # -------------------------------
    # Final Output
    # -------------------------------

    print("\n===== FINAL RESULT =====")
    print(result)
    print("========================")
    return result
