from adapters.ocr_adapter import extract_text



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
