from enum import Enum

class DocumentType(str, Enum):
    DRIVERS_LICENSE = "drivers_license"
    PASSPORT = "passport"
    SSN_CARD = "ssn_card"
    W2 = "w2"
    PAYSTUB = "paystub"
    BANK_STATEMENT = "bank_statement"
    UNKNOWN = "unknown"
