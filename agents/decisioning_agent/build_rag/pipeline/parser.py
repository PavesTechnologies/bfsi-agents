"""
STAGE 1: Parse raw PDFs into typed elements.

unstructured.io runs a layout detection model (detectron2/YOLOX) to tag
each region as Title / NarrativeText / Table / ListItem, preserving the
structure that flat text extraction (PyPDF2, pdfminer) loses.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging

from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx

logger = logging.getLogger(__name__)


@dataclass
class ParsedElement:
    element_type: str
    text: str
    page_number: int
    element_id: str

    table_html: Optional[str] = None
    table_data: Optional[list] = None

    coordinates: Optional[dict] = None


def parse_document(file_path: str) -> list[ParsedElement]:
    """
    Parse a PDF or DOCX into typed elements.

    strategy="hi_res" activates the layout detection model — without
    it, headings and body text become indistinguishable.
    """
    path = Path(file_path)

    if path.suffix.lower() == ".pdf":
        raw_elements = partition_pdf(
            filename=str(path),
            # "fast" — pdfminer-only text extraction, no ML layout model, no OCR.
            # Sidesteps the hi_res / unstructured-inference / OCR stack on Windows.
            # Trade-off: tables come through as text, not Table elements.
            strategy="fast",
            include_page_breaks=True,
            extract_images_in_pdf=False,
        )
    elif path.suffix.lower() == ".docx":
        raw_elements = partition_docx(
            filename=str(path),
            infer_table_structure=True,
        )
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    parsed = []
    for elem in raw_elements:
        page_num = elem.metadata.page_number if elem.metadata.page_number else 0
        pe = ParsedElement(
            element_type=elem.category,
            text=str(elem),
            page_number=page_num,
            element_id=elem.id,
        )

        if elem.category == "Table":
            pe.table_html = getattr(elem.metadata, "text_as_html", None)
            pe.table_data = _parse_table_html(pe.table_html)

        coords = getattr(elem.metadata, "coordinates", None)
        if coords and getattr(coords, "points", None):
            pe.coordinates = {
                "x": coords.points[0][0],
                "y": coords.points[0][1],
            }

        parsed.append(pe)

    table_count = sum(1 for e in parsed if e.element_type == "Table")
    logger.info(
        "Parsed %s: %d elements (%d tables)",
        path.name, len(parsed), table_count,
    )

    return parsed


def _parse_table_html(html: Optional[str]) -> Optional[list[dict]]:
    """Convert table HTML to list of row-dicts. Returns None on any failure."""
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
