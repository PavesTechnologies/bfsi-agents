## 1. Mock Applicant Data (Input Payloads)

These payloads follow the 5.1 Structured Inputs schema from your PRD.

**Case A: The "Golden Path" (Legitimate Applicant)**

> Target Outcome: PASS

```json
{
  "applicant_id": "c1914cdd-7d27-47eb-8732-388dd0963a35",
  "full_name": "John Quincy Public",
  "dob": "1985-05-15",
  "ssn": "666451234",
  "address": {
    "line1": "1600 Pennsylvania Avenue NW",
    "line2": "1600 Pennsylvania Avenue NW",
    "city": "Washington",
    "state": "DC",
    "zip": "20500"
  },
  "phone": "+12024561111",
  "email": "jq.public@example.com",
  "idempotency_key": "c1914cdd-7d27-47eb-8732-388dd0963a35"
}
```

**Case B: Synthetic Identity / SSN Mismatch**

> Target Outcome: FAIL or NEEDS_HUMAN_REVIEW

Reason: SSN issued before DOB or name mismatch.

```JSON
{
  "applicant_id": "user_1234",
  "full_name": "Scammy McFraud",
  "dob": "2005-01-01",
  "ssn": "000123456",
  "address": {
    "line1": "123 Ghost St",
    "line2": "No where",
    "city": "Nowhere",
    "state": "KS",
    "zip": "00000"
  },
    "phone": "+12024561111",
    "email": "jq.public@example.com",
    "idempotency_key":"c1914cdd-7d27-47eb-8732-388dd0963a35"
}
```
