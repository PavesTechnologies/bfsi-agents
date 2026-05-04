import re
from typing import Optional

from .utils import normalize_name

_PARSE_DOB_RE = re.compile(r'^(\d{2})/(\d{2})/(\d{4})$')


def _parse_pan_dob(raw: Optional[str]) -> Optional[str]:
    """Convert DD/MM/YYYY → YYYY-MM-DD."""
    if not raw:
        return None
    m = _PARSE_DOB_RE.match(raw.strip())
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return None


class PANNormalizer:
    def normalize(self, ocr_result: dict) -> dict:
        """
        Map validate_pan_ocr output to the internal cross-validation schema.
        """
        return {
            "document_type": "pan_card",
            "pan_number": ocr_result.get("pan_number"),
            "full_name": normalize_name(ocr_result.get("name")),
            "date_of_birth": _parse_pan_dob(ocr_result.get("dob")),
        }
