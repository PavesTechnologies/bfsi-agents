"""
STAGE 1: Parse raw PDFs into typed elements using pdfminer.six.

Uses character-level font metadata to classify text blocks as
Title / NarrativeText / ListItem â€” no ML models, no unstructured_inference
dependency. Works correctly for text-based PDFs (e.g. reportlab-generated
policy documents).

Classification rules (matching our reportlab PDF styles):
  - Helvetica-Bold OR Courier-Bold, fontSize >= 10  â†’  Title
  - Helvetica-Bold, fontSize < 10                   â†’  Title  (node-tag / sub-heading)
  - Text starting with "- " or "* "                 â†’  ListItem
  - Everything else                                 â†’  NarrativeText

DOCX files still use python-docx (no inference dependency).
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ParsedElement:
    element_type: str      # "Title" | "NarrativeText" | "ListItem" | "Table"
    text: str
    page_number: int
    element_id: str

    table_html: Optional[str] = None
    table_data: Optional[list] = None
    coordinates: Optional[dict] = None


# â”€â”€ PDF parsing via pdfminer.six â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _dominant_font(ltbox) -> tuple[str, float]:
    """
    Return (fontname, fontsize) of the most-used character in the box.
    Falls back to ("", 0) when no character info is available.
    """
    from pdfminer.layout import LTChar, LTTextLine

    counts: dict[tuple, int] = {}
    for line in ltbox:
        if not isinstance(line, LTTextLine):
            continue
        for ch in line:
            if isinstance(ch, LTChar):
                key = (ch.fontname, round(ch.size, 1))
                counts[key] = counts.get(key, 0) + 1

    if not counts:
        return ("", 0.0)
    return max(counts, key=counts.__getitem__)


def _classify(text: str, fontname: str, fontsize: float) -> str:
    """Map font + text content to an element_type string."""
    stripped = text.strip()
    is_bold = "Bold" in fontname or "bold" in fontname

    # Headings: bold text of any size OR large text
    if is_bold and fontsize >= 8:
        return "Title"
    if fontsize >= 11:
        return "Title"

    # List items
    if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("â€¢ "):
        return "ListItem"

    # Numbered list "1. " or "(a) "
    if re.match(r"^(\d+\.\s|[a-z]\)\s|\([a-z]\)\s)", stripped):
        return "ListItem"

    return "NarrativeText"


def _parse_pdf(file_path: str) -> list[ParsedElement]:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextBox, LTFigure, LTLayoutContainer

    elements: list[ParsedElement] = []
    elem_counter = 0

    for page_num, page_layout in enumerate(extract_pages(file_path), start=1):
        for element in page_layout:
            if not isinstance(element, LTTextBox):
                continue

            text = element.get_text().strip()
            if not text:
                continue

            fontname, fontsize = _dominant_font(element)
            etype = _classify(text, fontname, fontsize)

            # Split multi-line boxes at natural newline boundaries so that
            # heading lines are not fused with body text.
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            for line in lines:
                fn, fs = fontname, fontsize
                et = _classify(line, fn, fs)
                elements.append(ParsedElement(
                    element_type=et,
                    text=line,
                    page_number=page_num,
                    element_id=f"elem_{elem_counter}",
                    coordinates={
                        "x": round(element.x0, 1),
                        "y": round(element.y0, 1),
                    },
                ))
                elem_counter += 1

    return elements


# â”€â”€ DOCX parsing via python-docx â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _parse_docx(file_path: str) -> list[ParsedElement]:
    try:
        import docx
    except ImportError:
        raise RuntimeError(
            "python-docx is required for DOCX parsing. "
            "Install it: pip install python-docx"
        )

    doc = docx.Document(file_path)
    elements: list[ParsedElement] = []
    page_num = 1

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue

        style_name = (para.style.name or "").lower()
        if "heading" in style_name or "title" in style_name:
            etype = "Title"
        elif text.startswith("- ") or text.startswith("â€¢ "):
            etype = "ListItem"
        else:
            etype = "NarrativeText"

        elements.append(ParsedElement(
            element_type=etype,
            text=text,
            page_number=page_num,
            element_id=f"elem_{i}",
        ))

    return elements


# â”€â”€ Public interface â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def parse_document(file_path: str) -> list[ParsedElement]:
    """Parse a PDF or DOCX file into typed ParsedElement objects."""
    path = Path(file_path)

    if path.suffix.lower() == ".pdf":
        parsed = _parse_pdf(str(path))
    elif path.suffix.lower() == ".docx":
        parsed = _parse_docx(str(path))
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    table_count = sum(1 for e in parsed if e.element_type == "Table")
    logger.info(
        "Parsed %s: %d elements (%d tables)",
        path.name, len(parsed), table_count,
    )
    return parsed


def _parse_table_html(html: Optional[str]) -> Optional[list[dict]]:
    """Convert table HTML to list of row-dicts. Kept for DOCX compatibility."""
    if not html:
        return None
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            return None
        header_row = table.find("tr")
        if not header_row:
            return None
        headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
        if not headers:
            return None
        rows = []
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
        return rows or None
    except Exception as exc:
        logger.warning("Table HTML parse failed: %s", exc)
        return None

