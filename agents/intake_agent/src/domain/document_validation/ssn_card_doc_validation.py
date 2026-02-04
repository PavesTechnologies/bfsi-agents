import os
import base64
import time
from ollama import chat
import re

def has_ssn_number(text):
    """Check SSN number format"""
    return bool(re.search(r"\b\d{3}-\d{2}-\d{4}\b", text))


def has_ssn_keywords(text):
    """Check SSN-related keywords"""
    keywords = [
        "social security",
        "ssa",
        "social security administration",
        "signature"
    ]

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


def validate_ssn(text):

    has_number = has_ssn_number(text)
    has_keywords = has_ssn_keywords(text)

    confidence = calculate_confidence(text)

    is_valid = (
        has_number and has_keywords and
        confidence >= 0.8
    )

    return {
        "doc_type": "SSN" if is_valid else "INVALID",
        "confidence": round(confidence, 3),
        "valid": is_valid
    }


# -------------------------------
# OCR + Validation Pipeline
# -------------------------------

def ssn_card_validation(processed_image_bytes):
    
    # 3️⃣ Convert PROCESSED image to base64
    processed_image_base64 = base64.b64encode(processed_image_bytes).decode("utf-8")
    
    start_time = time.time()
    print(f"Processing image...")
    # Send to Ollama OCR
    response = chat(
        model="glm-ocr",
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract all readable text from this image. "
                    "If the text is clear, return ONLY the extracted text. "
                    "If not readable, return exactly: 'Failed to retrieved context', and nothing else."
                    "Also return the confidence level of the extraction."
                ),
                "images": [processed_image_base64]
            }
        ],
    )

    ocr_text = response.message.content.strip()

    print("\n===== OCR TEXT =====")
    print(ocr_text)
    print("====================")

    # Validate SSN
    result = validate_ssn(ocr_text)

    end_time = time.time()

    # -------------------------------
    # Final Output
    # -------------------------------

    print("\n===== FINAL RESULT =====")
    print(result)
    print("========================")

    print(f"Time taken: {round(end_time - start_time, 2)} seconds")

    return result
