import base64
import time

from ollama import chat


def ocr_text_extraction_from_image_bytes(processed_image_bytes):
    # 3️⃣ Convert PROCESSED image to base64
    processed_image_base64 = base64.b64encode(processed_image_bytes).decode("utf-8")

    start_time = time.time()
    print("Processing image...")
    # Send to Ollama OCR
    response = chat(
        model="glm-ocr",
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract all readable text from this image. "
                    "If the text is clear, return ONLY the extracted text. "
                    "If not readable, return exactly: 'Failed to retrieved context',\
                          and nothing else."
                    "Also return the confidence level of the extraction."
                ),
                "images": [processed_image_base64],
            }
        ],
    )

    ocr_text = response.message.content.strip()

    end_time = time.time()
    print("\n===== OCR TEXT =====")
    print(ocr_text)
    print("====================")
    print(f"Time taken: {round(end_time - start_time, 2)} seconds")
    return ocr_text
