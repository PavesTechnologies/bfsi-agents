"""Mock External Enrichment Adapters - Architecture Documentation

This document describes the mock external enrichment adapters implemented for the
loan intake validation system. These adapters provide deterministic mock behavior
for testing and can be replaced with real HTTP integrations later.

═══════════════════════════════════════════════════════════════════════════════
DESIGN PRINCIPLES
═══════════════════════════════════════════════════════════════════════════════

1. STATELESS
   - No instance variables
   - All methods are static
   - Multiple instances produce identical results

2. NO DATABASE ACCESS
   - Adapters are pure functions
   - No ORM interactions
   - No query execution

3. NO FASTAPI DEPENDENCIES
   - No Request, Response, HTTPException
   - No async/await (all synchronous)
   - Can be used outside FastAPI context

4. NO BUSINESS RULES
   - Adapters don't make business decisions
   - They only transform data
   - No validation errors raised

5. DETERMINISTIC MOCK BEHAVIOR
   - Same input always produces same output
   - Predictable for testing
   - No random or time-dependent behavior

6. ONE PUBLIC METHOD PER ADAPTER
   - Single entry point per adapter
   - Clear, focused responsibility
   - Easy to understand and maintain

═══════════════════════════════════════════════════════════════════════════════
ADAPTER DIRECTORY STRUCTURE
═══════════════════════════════════════════════════════════════════════════════

src/adapters/http/
├── usps/                          # USPS Address Verification
│   ├── __init__.py
│   ├── interfaces.py              # Input/output dataclasses
│   └── mock_adapter.py            # Implementation
│   └── tests/
│       ├── __init__.py
│       └── test_mock_usps_adapter.py
│
├── employer/                      # Employer Verification
│   ├── __init__.py
│   ├── interfaces.py
│   └── mock_adapter.py
│   └── tests/
│       ├── __init__.py
│       └── test_mock_employer_adapter.py
│
├── phone/                         # Phone Intelligence
│   ├── __init__.py
│   ├── interfaces.py
│   └── mock_adapter.py
│   └── tests/
│       ├── __init__.py
│       └── test_mock_phone_adapter.py
│
└── email/                         # Email Domain Risk
    ├── __init__.py
    ├── interfaces.py
    └── mock_adapter.py
    └── tests/
        ├── __init__.py
        └── test_mock_email_adapter.py

═══════════════════════════════════════════════════════════════════════════════
ADAPTER SPECIFICATIONS
═══════════════════════════════════════════════════════════════════════════════

1. USPS ADDRESS VERIFICATION
───────────────────────────────────────────────────────────────────────────────

   Location: src/adapters/http/usps/

   Method: MockUSPSAdapter.verify_address(address_input: USPSAddressInput)
           → USPSAddressResult

   Input Fields:
   - address_line1 (str, required): Primary address line
   - address_line2 (str, optional): Secondary address line (Apt, Suite, etc.)
   - city (str, optional): City name
   - state (str, optional): State code
   - zip_code (str, optional): ZIP code

   Output Fields:
   - deliverable (bool): Whether address is deliverable
   - standardized_address (str, optional): Normalized address format
   - zip5 (str, optional): 5-digit ZIP code
   - zip4 (str, optional): 4-digit ZIP extension
   - confidence (float): Confidence level 0.0–1.0

   Mock Logic:
   - Empty address_line1 → deliverable=False, confidence=0.0
   - Valid address_line1 → deliverable=True, zip4="1234", confidence=0.9

   Example:
   ```python
   from src.adapters.http.usps import MockUSPSAdapter, USPSAddressInput

   adapter = MockUSPSAdapter()
   result = adapter.verify_address(
       USPSAddressInput(
           address_line1="123 Main St",
           city="New York",
           state="NY",
           zip_code="10001"
       )
   )
   # result.deliverable == True
   # result.confidence == 0.9
   ```

───────────────────────────────────────────────────────────────────────────────

2. EMPLOYER VERIFICATION
───────────────────────────────────────────────────────────────────────────────

   Location: src/adapters/http/employer/

   Method: MockEmployerAdapter.verify_employer(employer_input: EmployerInput)
           → EmployerVerificationResult

   Input Fields:
   - employer_name (str, required): Company name
   - employer_phone (str, optional): Contact phone number
   - employer_address (str, optional): Business address

   Output Fields:
   - verified (bool): Whether employer is verified/legitimate
   - normalized_name (str, optional): Standardized company name
   - naics_code (str, optional): North American Industry Code
   - confidence (float): Confidence level 0.0–1.0

   Mock Logic:
   - Empty employer_name → verified=False, confidence=0.0
   - Name contains inc|corp|llc|ltd|gmbh|sa|ag (case-insensitive)
     → verified=True, naics_code="541512", confidence=0.85
   - Otherwise → verified=False, confidence=0.0

   Example:
   ```python
   from src.adapters.http.employer import MockEmployerAdapter, EmployerInput

   adapter = MockEmployerAdapter()
   result = adapter.verify_employer(
       EmployerInput(employer_name="Acme Corporation")
   )
   # result.verified == True
   # result.naics_code == "541512"
   ```

───────────────────────────────────────────────────────────────────────────────

3. PHONE INTELLIGENCE
───────────────────────────────────────────────────────────────────────────────

   Location: src/adapters/http/phone/

   Method: MockPhoneAdapter.analyze_phone(phone_input: PhoneInput)
           → PhoneIntelligenceResult

   Input Fields:
   - phone_number (str): Phone number to analyze

   Output Fields:
   - valid (bool): Whether phone is valid
   - line_type (str): "mobile" or "unknown"
   - carrier (str, optional): Carrier name (mock: "Mock Carrier")
   - confidence (float): Confidence level 0.0–1.0

   Mock Logic:
   - Empty phone_number → valid=False, confidence=0.0
   - After stripping non-numeric chars:
     - < 10 digits → valid=False, line_type="unknown", confidence=0.0
     - >= 10 digits → valid=True, line_type="mobile", confidence=0.92

   Example:
   ```python
   from src.adapters.http.phone import MockPhoneAdapter, PhoneInput

   adapter = MockPhoneAdapter()
   result = adapter.analyze_phone(
       PhoneInput(phone_number="+1-555-0100")
   )
   # result.valid == True
   # result.line_type == "mobile"
   ```

───────────────────────────────────────────────────────────────────────────────

4. EMAIL DOMAIN RISK
───────────────────────────────────────────────────────────────────────────────

   Location: src/adapters/http/email/

   Method: MockEmailAdapter.analyze_email_domain(email_input: EmailInput)
           → EmailRiskResult

   Input Fields:
   - email (str): Email address to analyze

   Output Fields:
   - domain (str): Extracted domain
   - risk (str): "low", "medium", or "high"
   - disposable (bool): Whether domain is disposable/temporary
   - confidence (float): Confidence level 0.0–1.0

   Mock Logic:
   - Low Risk (confidence 0.95):
     * gmail.com, outlook.com, yahoo.com, icloud.com
   - High Risk (confidence 0.98):
     * mailinator.com, tempmail.com, guerrillamail.com → disposable=True
   - Medium Risk (confidence 0.80):
     * All other domains
   - Invalid Email:
     * Empty string or no @ symbol → risk="high", disposable=True

   Example:
   ```python
   from src.adapters.http.email_risk import MockEmailAdapter, EmailInput

   adapter = MockEmailAdapter()
   result = adapter.analyze_email_domain(
       EmailInput(email="user@gmail.com")
   )
   # result.domain == "gmail.com"
   # result.risk == "low"
   # result.disposable == False
   ```

═══════════════════════════════════════════════════════════════════════════════
TESTING STRATEGY
═══════════════════════════════════════════════════════════════════════════════

Each adapter includes comprehensive pytest test suite covering:

1. Valid Input Scenarios
   - Standard valid inputs return expected results
   - Edge cases handled correctly

2. Invalid Input Scenarios
   - Empty/None values handled gracefully
   - Malformed data produces predictable output

3. Output Shape Validation
   - All expected fields exist
   - Correct data types
   - Confidence values in valid range (0.0–1.0)

4. Statelessness Testing
   - Multiple calls with same input produce identical results
   - No state mutations

5. Error Resilience
   - No exceptions raised for edge cases
   - Graceful degradation

Run tests:
```bash
pytest src/adapters/http/usps/tests/test_mock_usps_adapter.py
pytest src/adapters/http/employer/tests/test_mock_employer_adapter.py
pytest src/adapters/http/phone/tests/test_mock_phone_adapter.py
pytest src/adapters/http/email/tests/test_mock_email_adapter.py

# Or all at once:
pytest src/adapters/http/
```

═══════════════════════════════════════════════════════════════════════════════
USAGE IN VALIDATION PIPELINE
═══════════════════════════════════════════════════════════════════════════════

These adapters are meant to be integrated into the validation/enrichment pipeline:

```python
from src.adapters.http.usps import MockUSPSAdapter, USPSAddressInput
from src.adapters.http.employer import MockEmployerAdapter, EmployerInput

# Enrich address data
usps_adapter = MockUSPSAdapter()
address_result = usps_adapter.verify_address(
    USPSAddressInput(
        address_line1=applicant.address.address_line1,
        city=applicant.address.city,
        state=applicant.address.state,
        zip_code=applicant.address.zip_code
    )
)

# Verify employment
employer_adapter = MockEmployerAdapter()
employer_result = employer_adapter.verify_employer(
    EmployerInput(
        employer_name=applicant.employment.employer_name
    )
)

# Use results in business logic
if not address_result.deliverable:
    # Handle invalid address
    pass

if not employer_result.verified:
    # Flag for manual review
    pass
```

═══════════════════════════════════════════════════════════════════════════════
FUTURE INTEGRATION ROADMAP
═══════════════════════════════════════════════════════════════════════════════

1. CREATE REAL ADAPTER INTERFACES
   - Define abstract base classes
   - Ensure compatibility with mock adapters

2. IMPLEMENT HTTP CLIENTS
   - USPS Web Tools API
   - Employer verification services
   - Carrier lookup APIs
   - Email reputation services

3. ADD RETRIES & TIMEOUTS
   - Circuit breaker pattern
   - Exponential backoff
   - Request timeouts

4. IMPLEMENT CACHING
   - Redis cache for common lookups
   - TTL-based expiration

5. ADD LOGGING & MONITORING
   - Adapter call tracking
   - Performance metrics
   - Error alerting

═══════════════════════════════════════════════════════════════════════════════
KEY CHARACTERISTICS SUMMARY
═══════════════════════════════════════════════════════════════════════════════

┌─ USPS Adapter ───────────────────────────────────────────────────────────┐
│ Public Method:  verify_address(USPSAddressInput) → USPSAddressResult    │
│ Mock Logic:     Empty line1 → not deliverable, else deliverable         │
│ Input Ports:    address_line1, address_line2, city, state, zip_code    │
│ Output Ports:   deliverable, standardized_address, zip5, zip4, confidence
└──────────────────────────────────────────────────────────────────────────┘

┌─ Employer Adapter ────────────────────────────────────────────────────────┐
│ Public Method:  verify_employer(EmployerInput) → EmployerVerificationResult
│ Mock Logic:     Contains keyword (inc|corp|llc|...) → verified         │
│ Input Ports:    employer_name, employer_phone, employer_address       │
│ Output Ports:   verified, normalized_name, naics_code, confidence     │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Phone Adapter ───────────────────────────────────────────────────────────┐
│ Public Method:  analyze_phone(PhoneInput) → PhoneIntelligenceResult    │
│ Mock Logic:     >= 10 digits → valid, else invalid                    │
│ Input Ports:    phone_number                                            │
│ Output Ports:   valid, line_type, carrier, confidence                 │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Email Adapter ───────────────────────────────────────────────────────────┐
│ Public Method:  analyze_email_domain(EmailInput) → EmailRiskResult     │
│ Mock Logic:     Domain in known list → specific risk level            │
│ Input Ports:    email                                                   │
│ Output Ports:   domain, risk, disposable, confidence                  │
└──────────────────────────────────────────────────────────────────────────┘
"""
