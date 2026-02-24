import re

from .utils import (
    normalize_country,
    normalize_date,
    normalize_name,
    normalize_sex,
)

PASSPORT_NUMBER_REGEX = re.compile(r"^[A-Z0-9]{6,9}$")


class PassportNormalizer:
    def normalize(self, data: dict) -> dict:
        """
        Normalize MRZ-extracted passport data (passport fields only)
        """

        return {
            # -----------------------------
            # Document metadata
            # -----------------------------
            "document_type": "PASSPORT",
            # "document_subtype": data.get("document_type"),  # P
            #
            "issuing_country": normalize_country(data.get("country")),
            "nationality": normalize_country(data.get("nationality")),
            # -----------------------------
            # Names
            # -----------------------------
            "last_name": normalize_name(data.get("surname")),
            "first_name": normalize_name(data.get("given_name")),
            # -----------------------------
            # Passport details
            # -----------------------------
            "passport_number": self._normalize_passport_number(
                data.get("passport_number")
            ),
            # -----------------------------
            # Personal attributes
            # -----------------------------
            "date_of_birth": normalize_date(data.get("date_of_birth")),
            "expiry_date": normalize_date(data.get("expiry_date")),
            "gender": self._normalize_gender(data.get("gender")),
        }

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _normalize_passport_number(self, value: str | None) -> str | None:
        if not value:
            return None

        value = value.upper().replace(" ", "")
        return value if PASSPORT_NUMBER_REGEX.match(value) else None

    def _normalize_gender(self, value: str | None) -> str | None:
        if not value:
            return None

        value = value.strip().upper()

        if value == "<":
            return "UNSPECIFIED"

        return normalize_sex(value)
