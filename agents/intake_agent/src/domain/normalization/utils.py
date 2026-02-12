import re
from typing import Optional


# -----------------------------
# Name helpers
# -----------------------------

def normalize_name(value: Optional[str]) -> Optional[str]:
    """
    Uppercase, strip punctuation, collapse spaces.
    """
    if not value:
        return None

    value = value.upper()
    value = re.sub(r"[^\w\s]", "", value)  # remove punctuation
    value = re.sub(r"\s+", " ", value).strip()

    return value

def normalize_sex(value: Optional[str]) -> Optional[str]:
    """
    Normalize sex/gender values.
    Common DL values:
    - 1 / M → MALE
    - 2 / F → FEMALE
    """
    if not value:
        return None

    value = value.strip().upper()

    if value in {"1", "M", "MALE"}:
        return "MALE"
    if value in {"2", "F", "FEMALE"}:
        return "FEMALE"

    return value

def split_full_name(full_name: Optional[str]) -> dict:
    """
    Split FULL NAME into first / middle / last (best-effort).
    """
    if not full_name:
        return {"first_name": None, "middle_name": None, "last_name": None}

    parts = full_name.split(" ")

    if len(parts) == 1:
        return {"first_name": parts[0], "middle_name": None, "last_name": None}

    if len(parts) == 2:
        return {"first_name": parts[0], "middle_name": None, "last_name": parts[1]}

    return {
        "first_name": parts[0],
        "middle_name": " ".join(parts[1:-1]),
        "last_name": parts[-1],
    }


# -----------------------------
# Address helpers
# -----------------------------

ADDRESS_ABBREVIATIONS = {
    "STREET": "ST",
    "ROAD": "RD",
    "AVENUE": "AVE",
    "BOULEVARD": "BLVD",
    "DRIVE": "DR",
    "LANE": "LN",
    "COURT": "CT",
}
def normalize_country(value: Optional[str]) -> Optional[str]:
    """
    Normalize country names to ISO-style uppercase.
    """
    if not value:
        return None

    value = normalize_name(value)

    COUNTRY_MAP = {
        "USA": "USA",
        "UNITED STATES": "USA",
        "UNITED STATES OF AMERICA": "USA",
        "US": "USA",
    }

    return COUNTRY_MAP.get(value, value)


def expand_address_abbreviations(address: Optional[str]) -> Optional[str]:
    """
    Normalize address words (STREET -> ST, ROAD -> RD, etc).
    """
    if not address:
        return None

    address = address.upper()

    # for long, short in ADDRESS_ABBREVIATIONS.items():
    #     address = re.sub(rf"\b{long}\b", short, address)

    address = re.sub(r"\s+", " ", address).strip()
    return address


def normalize_zip(zip_code: Optional[str]) -> Optional[str]:
    """
    Normalize ZIP to:
    - 12345
    - 12345-6789
    """
    if not zip_code:
        return None

    digits = re.sub(r"[^\d]", "", zip_code)

    if len(digits) == 5:
        return digits

    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"

    return None


def canonical_address(
    line1: Optional[str],
    city: Optional[str],
    state: Optional[str],
    zip_code: Optional[str],
) -> dict:
    """
    Canonical structured address format.
    """
    return {
        "line1": expand_address_abbreviations(line1),
        "city": normalize_name(city),
        "state": normalize_name(state),
        "zip": normalize_zip(zip_code),
    }
def normalize_date(value: Optional[str]) -> Optional[str]:
    """
    Ensures YYYY-MM-DD format if already close.
    (Assumes OCR gives ISO-ish values)
    """
    if not value:
        return None

    value = value.strip()

    if re.match(r"\d{4}-\d{2}-\d{2}", value):
        return value

    return None
