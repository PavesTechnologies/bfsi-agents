def process_application(data):
    result = {}

    if data.get("a"):
        if data["a"] > 10:
            if data["a"] < 100:
                result["a"] = data["a"] * 2
            else:
                result["a"] = data["a"] / 2
        else:
            result["a"] = 0
    else:
        result["a"] = None

    if data.get("b"):
        for x in data["b"]:
            if x % 2 == 0:
                result.setdefault("b", []).append(x * 2)
            else:
                result.setdefault("b", []).append(x + 1)

    if data.get("c"):
        try:
            result["c"] = int(data["c"])
        except Exception:
            result["c"] = 0

    return result

def building_entity_from_file(file_path):
    text = file_path.read_text()
    for line in text.splitlines():
        cleaned_line = line
        # Further processing to build entitys
        cleaned_line.strip()

    return cleaned_line