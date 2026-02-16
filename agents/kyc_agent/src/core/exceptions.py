class KYCBaseException(Exception):
    """Base class for all KYC Agent exceptions."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class KYCValidationError(KYCBaseException):
    """Raised when intake data (SSN, DOB) fails format validation."""
    def __init__(self, message: str = "Invalid input data"):
        super().__init__(message, status_code=422)

class VendorTimeoutError(KYCBaseException):
    """Raised when an external identity or AML vendor fails to respond."""
    def __init__(self, vendor_name: str):
        super().__init__(f"Vendor {vendor_name} timed out", status_code=504)

class ComplianceHardFail(KYCBaseException):
    """Raised for critical compliance failures like OFAC hits or Spoofing."""
    def __init__(self, reason: str):
        # Maps to kyc_status = FAIL
        super().__init__(f"Compliance Hard Stop: {reason}", status_code=200)