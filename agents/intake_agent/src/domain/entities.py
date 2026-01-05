from adapters.ocr_adapter import extract_text

def building_entity_from_file(file_path):
    txt = extract_text(file_path)
    return {"text": txt}
