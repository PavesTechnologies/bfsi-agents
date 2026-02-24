from datetime import datetime
from typing import Any

from .base import BaseNormalizer
from .utils import (
    canonical_address,
    normalize_country,
    normalize_name,
    normalize_sex,
    split_full_name,
)


class DriversLicenseNormalizer(BaseNormalizer):
    """
    Normalizes Drivers License extracted fields into canonical format.
    """

    def parse_date(self, value):
        # Common AAMVA date formats: MMDDYYYY or YYYYMMDD
        for fmt in ("%m%d%Y", "%Y%m%d"):
            try:
                return datetime.strptime(value, fmt).date().isoformat()
            except Exception as e:
                print(e)
                print(f"Date parsing failed for value: {value} with format {fmt}")
                continue
        return value

    def normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        # -----------------------------
        # Name normalization
        # -----------------------------

        full_name = normalize_name(data.get("full_name"))

        if full_name:
            name_parts = split_full_name(full_name)
        else:
            name_parts = {
                "first_name": normalize_name(data.get("first_name")),
                "middle_name": normalize_name(data.get("middle_name")),
                "last_name": normalize_name(data.get("last_name")),
            }

        # -----------------------------
        # Address normalization
        # -----------------------------

        address = canonical_address(
            line1=data.get("street_address"),
            city=data.get("city"),
            state=data.get("state"),
            zip_code=data.get("postal_code"),
        )

        # -----------------------------
        # Canonical output
        # -----------------------------

        return {
            "document_type": "drivers_license",
            "name": name_parts,
            "dob": self.parse_date(data.get("date_of_birth")),
            "license_number": normalize_name(data.get("license_number")),
            "address": address,
            "issue_date": self.parse_date(data.get("issue_date")),
            "expiry_date": self.parse_date(data.get("expiry_date")),
            "gender": normalize_sex(data.get("sex")),
            "country": normalize_country(data.get("country")),
            "issuing_state": normalize_name(data.get("state")),
        }
