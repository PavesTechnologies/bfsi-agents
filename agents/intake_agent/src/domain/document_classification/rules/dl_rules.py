import re


# Explicit DL / ID phrases (must be strong, not fuzzy)
DL_KEYWORDS = [
    "DRIVER LICENSE",
    "DRIVER LICENCE",
    "DRIVER'S LICENSE",
    "DRIVING LICENCE",
]

# Mandatory identity-related fields
MANDATORY_FIELDS = [
    "DATE OF BIRTH",
    "DOB",
    "EXPIRATION",
    "EXPIRES",
    "ISSUED",
]

# US State codes (used only as a weak supporting signal)
US_STATE_CODES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
}


def match(text: str, ocr_blocks=None) -> float:
    """
    Driver License classification rules.

    STRICT POLICY:
    - Must have an explicit DL keyword
    - Must have at least TWO mandatory identity fields
    - State code alone can never trigger classification
    """

    if not text:
        return 0.0

    text = text.upper()
    score = 0.0

    # ---------- Hard requirement 1: explicit DL keyword ----------
    if not any(k in text for k in DL_KEYWORDS):
        return 0.0  # fail fast

    score += 0.4

    # ---------- Hard requirement 2: identity fields ----------
    mandatory_hits = sum(1 for f in MANDATORY_FIELDS if f in text)

    if mandatory_hits < 2:
        return 0.0  # not a real DL

    score += 0.4

    # ---------- Supporting signal: US state ----------
    if any(re.search(rf"\b{state}\b", text) for state in US_STATE_CODES):
        score += 0.1

    # ---------- Supporting signal: license number pattern ----------
    if re.search(r"\b(LIC|LICENSE)[\s#:]*[A-Z0-9]{5,}\b", text):
        score += 0.1

    return min(score, 1.0)
