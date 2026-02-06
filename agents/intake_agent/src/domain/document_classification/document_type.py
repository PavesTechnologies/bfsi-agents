from enum import Enum

class DocumentType(str, Enum):
    DRIVERS_LICENSE = "drivers_license"
    PASSPORT = "passport"
    SSN_CARD = "ssn_card"
    W2 = "w2"
    PAY_STUB = "pay_stub"
    # backward-compatible alias
    PAYSTUB = PAY_STUB
    BANK_STATEMENT = "bank_statement"
    UNKNOWN = "unknown"
