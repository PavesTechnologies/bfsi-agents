import re


class DataNormalizer:
    @staticmethod
    def normalize_string(value: str | None, uppercase: bool = False) -> str | None:
        if not value:
            return None
        stripped = value.strip()
        return stripped.upper() if uppercase else stripped

    @staticmethod
    def normalize_phone(phone: str) -> str:
        # Removes all non-numeric characters: (123) 456-7890 -> 1234567890
        return re.sub(r"\D", "", phone)

    @staticmethod
    def normalize_email(email: str | None) -> str | None:
        return email.strip().lower() if email else None

    @staticmethod
    def normalize_ssn(ssn: str | None) -> str | None:
        # Strip dashes if they exist
        return re.sub(r"\D", "", ssn) if ssn else None
