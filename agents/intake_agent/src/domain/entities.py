from adapters.ocr_adapter import extract_text

def building_entity_from_file(file_path):
    text = file_path.read_text()
    for line in text.splitlines():
        cleaned_line = extract_text(line)
        # Further processing to build entitys
        cleaned_line.strip()

    return cleaned_line
