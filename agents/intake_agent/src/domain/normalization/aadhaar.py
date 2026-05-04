import re
from typing import Optional

from .utils import normalize_name

_PARSE_DOB_RE = re.compile(r'^(\d{2})[-/](\d{2})[-/](\d{4})$')


def _parse_india_dob(raw: Optional[str]) -> Optional[str]:
    """Convert DD-MM-YYYY or DD/MM/YYYY → YYYY-MM-DD."""
    if not raw:
        return None
    m = _PARSE_DOB_RE.match(raw.strip())
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return None


class AadhaarNormalizer:
    def normalize(self, ocr_result: dict) -> dict:
        """
        Map validate_aadhaar_ocr output to the internal cross-validation schema.
        Fields that could not be extracted are set to None; the cross-validator
        skips None fields instead of raising false mismatches.
        """
        aadhaar_no = ocr_result.get("aadhaar_number")
        print(f"Normalizing Aadhaar OCR result: {ocr_result}")
        return {
            "document_type": "aadhaar_card",
            "aadhaar_last4": aadhaar_no[-4:] if aadhaar_no else None,
            "full_name": normalize_name(ocr_result.get("name")),
            "date_of_birth": _parse_india_dob(ocr_result.get("dob")),
            "gender": ocr_result.get("gender"),
        }
