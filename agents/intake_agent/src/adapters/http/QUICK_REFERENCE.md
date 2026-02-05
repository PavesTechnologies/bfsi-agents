"""Quick Reference - Mock Adapter Usage

═══════════════════════════════════════════════════════════════════════════════
QUICK IMPORT & USAGE PATTERNS
═══════════════════════════════════════════════════════════════════════════════

1. USPS ADDRESS VERIFICATION
─────────────────────────────────────────────────────────────────────────────
from src.adapters.http.usps import MockUSPSAdapter, USPSAddressInput

adapter = MockUSPSAdapter()
result = adapter.verify_address(
    USPSAddressInput(
        address_line1="123 Main St",
        address_line2="Apt 4B",
        city="New York",
        state="NY",
        zip_code="10001"
    )
)

# result.deliverable → bool
# result.standardized_address → str | None
# result.zip5 → str | None
# result.zip4 → str | None
# result.confidence → float (0.0–1.0)


2. EMPLOYER VERIFICATION
─────────────────────────────────────────────────────────────────────────────
from src.adapters.http.employer import MockEmployerAdapter, EmployerInput

adapter = MockEmployerAdapter()
result = adapter.verify_employer(
    EmployerInput(
        employer_name="Acme Inc",
        employer_phone="+1-555-0100",
        employer_address="100 Business Blvd"
    )
)

# result.verified → bool
# result.normalized_name → str | None
# result.naics_code → str | None
# result.confidence → float (0.0–1.0)


3. PHONE INTELLIGENCE
─────────────────────────────────────────────────────────────────────────────
from src.adapters.http.phone import MockPhoneAdapter, PhoneInput

adapter = MockPhoneAdapter()
result = adapter.analyze_phone(
    PhoneInput(phone_number="+1-555-0100")
)

# result.valid → bool
# result.line_type → "mobile" | "unknown"
# result.carrier → str | None
# result.confidence → float (0.0–1.0)


4. EMAIL DOMAIN RISK
─────────────────────────────────────────────────────────────────────────────
from src.adapters.http.email_risk import MockEmailAdapter, EmailInput

adapter = MockEmailAdapter()
result = adapter.analyze_email_domain(
    EmailInput(email="user@gmail.com")
)

# result.domain → str
# result.risk → "low" | "medium" | "high"
# result.disposable → bool
# result.confidence → float (0.0–1.0)

═══════════════════════════════════════════════════════════════════════════════
MOCK BEHAVIOR TRUTH TABLE
═══════════════════════════════════════════════════════════════════════════════

USPS ADDRESS VERIFICATION
─────────────────────────────────────────────────────────────────────────────
Input                           │ deliverable │ zip4   │ confidence
─────────────────────────────────────────────────────────────────────────────
Empty address_line1             │ False       │ None   │ 0.0
Valid address_line1             │ True        │ "1234" │ 0.9
Whitespace-only address_line1   │ False       │ None   │ 0.0

EMPLOYER VERIFICATION
─────────────────────────────────────────────────────────────────────────────
Input                           │ verified │ naics_code │ confidence
─────────────────────────────────────────────────────────────────────────────
Empty employer_name             │ False    │ None       │ 0.0
"Acme Inc" (has keyword)        │ True     │ "541512"   │ 0.85
"Joe's Pizza" (no keyword)      │ False    │ None       │ 0.0
"CORP Solutions" (keyword upper)│ True     │ "541512"   │ 0.85

PHONE INTELLIGENCE
─────────────────────────────────────────────────────────────────────────────
Input                           │ valid │ line_type │ carrier         │ confidence
─────────────────────────────────────────────────────────────────────────────
Empty string                    │ False │ "unknown" │ None            │ 0.0
"555-0100" (9 digits)           │ False │ "unknown" │ None            │ 0.0
"555-0100-1234" (10 digits)     │ True  │ "mobile"  │ "Mock Carrier"  │ 0.92
"+1-555-0100" (11 digits)       │ True  │ "mobile"  │ "Mock Carrier"  │ 0.92

EMAIL DOMAIN RISK
─────────────────────────────────────────────────────────────────────────────
Domain                  │ Risk    │ Disposable │ Confidence
─────────────────────────────────────────────────────────────────────────────
gmail.com               │ "low"   │ False      │ 0.95
outlook.com             │ "low"   │ False      │ 0.95
yahoo.com               │ "low"   │ False      │ 0.95
icloud.com              │ "low"   │ False      │ 0.95
mailinator.com          │ "high"  │ True       │ 0.98
tempmail.com            │ "high"  │ True       │ 0.98
guerrillamail.com       │ "high"  │ True       │ 0.98
company.com             │ "medium"│ False      │ 0.80
example.org             │ "medium"│ False      │ 0.80
Empty string            │ "high"  │ True       │ 0.0
No @ sign               │ "high"  │ True       │ 0.0

═══════════════════════════════════════════════════════════════════════════════
KEY FACTS
═══════════════════════════════════════════════════════════════════════════════

✓ All adapters are STATELESS
  → Same input always produces same output
  → No instance state maintained
  → Thread-safe

✓ No DATABASE ACCESS
  → Pure functions
  → No side effects
  → Can test in isolation

✓ No EXCEPTIONS RAISED
  → Graceful error handling
  → Returns default result for invalid input
  → Safe to use without try/except

✓ DETERMINISTIC BEHAVIOR
  → Predictable for testing
  → No randomness
  → No time-dependent logic

✓ SINGLE PUBLIC METHOD
  → One clear entry point per adapter
  → Easy to understand
  → Focused responsibility

═══════════════════════════════════════════════════════════════════════════════
RUNNING TESTS
═══════════════════════════════════════════════════════════════════════════════

# Run specific adapter tests
pytest src/adapters/http/usps/tests/
pytest src/adapters/http/employer/tests/
pytest src/adapters/http/phone/tests/
pytest src/adapters/http/email/tests/

# Run all adapter tests
pytest src/adapters/http/

# Run with verbose output
pytest -v src/adapters/http/

# Run with coverage
pytest --cov=src.adapters.http src/adapters/http/

═══════════════════════════════════════════════════════════════════════════════
COMMON USAGE PATTERN
═══════════════════════════════════════════════════════════════════════════════

def enrich_applicant_data(applicant):
    \"\"\"Enrich applicant data using mock adapters.\"\"\"
    
    # Address verification
    address_result = MockUSPSAdapter.verify_address(
        USPSAddressInput(
            address_line1=applicant.address.line1,
            city=applicant.address.city,
            state=applicant.address.state,
            zip_code=applicant.address.zip_code
        )
    )
    
    # Employer verification
    employer_result = MockEmployerAdapter.verify_employer(
        EmployerInput(
            employer_name=applicant.employment.employer_name
        )
    )
    
    # Phone intelligence
    phone_result = MockPhoneAdapter.analyze_phone(
        PhoneInput(
            phone_number=applicant.phone
        )
    )
    
    # Email risk assessment
    email_result = MockEmailAdapter.analyze_email_domain(
        EmailInput(
            email=applicant.email
        )
    )
    
    # Return enriched data
    return {
        "address": address_result,
        "employer": employer_result,
        "phone": phone_result,
        "email": email_result
    }

═══════════════════════════════════════════════════════════════════════════════
DATACLASS REFERENCE
═══════════════════════════════════════════════════════════════════════════════

All input/output are frozen dataclasses (immutable):

USPSAddressInput(
    address_line1: str,              # Required
    address_line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None
)

EmployerInput(
    employer_name: str,              # Required
    employer_phone: str | None = None,
    employer_address: str | None = None
)

PhoneInput(
    phone_number: str                # Required
)

EmailInput(
    email: str                       # Required
)

═══════════════════════════════════════════════════════════════════════════════
"""
