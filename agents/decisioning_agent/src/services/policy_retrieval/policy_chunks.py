"""Policy chunking helpers for local retrieval."""

from pathlib import Path


def chunk_policy_document(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    chunks = []
    current_section_id = "0"
    current_title = "Document Preamble"
    current_lines: list[str] = []

    def flush():
        if not current_lines:
            return
        chunks.append(
            {
                "section_id": current_section_id,
                "section_title": current_title,
                "content": "\n".join(current_lines).strip(),
            }
        )

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## ") or line.startswith("### "):
            flush()
            current_lines = []
            heading = line[3:].strip() if line.startswith("## ") else line[4:].strip()
            if " " in heading and heading.split(" ", 1)[0].replace(".", "").isdigit():
                current_section_id = heading.split(" ", 1)[0]
                current_title = heading.split(" ", 1)[1]
            else:
                current_section_id = heading
                current_title = heading
            continue
        current_lines.append(raw_line)

    flush()
    return chunks
