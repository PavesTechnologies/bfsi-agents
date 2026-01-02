
from adapters.ocr_adapter import extract_text


def build_entity_from_file(file_path):
    text = extract_text(file_path)
    if not text:
        raise ValueError("No text extracted")

    return {
        "raw_text": text,
        "length": len(text)
    }
