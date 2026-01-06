from pathlib import Path


def find_next_code_line(file_path: str, start_line: int) -> int | None:
    """
    Returns the first non-empty, non-whitespace line number
    at or after start_line (1-based).
    """
    try:
        lines = Path(file_path).read_text(
            encoding="utf-8",
            errors="ignore"
        ).splitlines()
    except Exception:
        return None

    for idx in range(start_line - 1, len(lines)):
        if lines[idx].strip():  # non-empty, non-whitespace
            return idx + 1

    return None
