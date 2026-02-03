Error Semantics & Validation Strategy
Purpose

This document defines how validation errors are detected, classified, stored, and surfaced in the Intake Agent.

The goal of error semantics is to capture data quality issues without blocking ingestion, enabling downstream decisioning, QA, and human review workflows.

This approach ensures:

No data loss

Full auditability

Clear separation between transport errors and domain validation findings

Core Principle

Data comes in dirty. We flag it — we do NOT reject it.

Invalid or suspicious input must not block intake, except when the API envelope itself is invalid.

Error Categories
1. Transport / Contract Errors (Blocking)

These errors occur before the intake job is accepted.

They result in HTTP 4xx responses and no async job is enqueued.

Examples:

Missing request_id

Invalid app_id type

Missing payload

Malformed JSON

Invalid UUID where required

These errors are enforced by Pydantic / FastAPI and represent API misuse, not data quality issues.

2. Domain Validation Errors (Non-Blocking)

These errors occur after the intake job is accepted and queued.

They:

Do not cause request rejection

Do not return HTTP errors

Are persisted for downstream use

Examples:

Invalid email format

Underage applicant

Invalid SSN last-4

Name containing numeric characters

Missing optional-but-relevant fields

These are semantic validation findings, not failures.

Validation Reason Codes

All domain validation findings are expressed as standardized reason codes.

Why reason codes exist

Machine-readable

Stable over time

Decoupled from human-readable messages

Safe for analytics and automation

Reason Code Structure

Reason codes are defined as enums.

Example:

class ValidationReasonCode(str, Enum):
    INVALID_FIRST_NAME = "INVALID_FIRST_NAME"
    INVALID_LAST_NAME = "INVALID_LAST_NAME"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_SSN_LAST4 = "INVALID_SSN_LAST4"
    AGE_BELOW_MINIMUM = "AGE_BELOW_MINIMUM"


Rules:

UPPER_SNAKE_CASE

No dynamic content

Never renamed once introduced

New codes are appended, not modified

Rule → Reason Code Mapping

Each validation rule must map to exactly one reason code.

Rule	Reason Code
First name contains digits	INVALID_FIRST_NAME
Last name contains digits	INVALID_LAST_NAME
Email fails regex	INVALID_EMAIL
SSN last-4 not numeric or length ≠ 4	INVALID_SSN_LAST4
Applicant age < 18	AGE_BELOW_MINIMUM

This mapping must remain deterministic.

Validation Execution Flow

Intake request is accepted (HTTP 202)

Async job begins processing

Validators are executed per field

Each failed rule produces a reason code

All reason codes are collected

Results are persisted

Processing continues regardless of failures

No rule may throw an exception that halts intake.

Persistence Model

All validation findings are persisted in an append-only table.

Example Table: intake_validation_result
Column	Purpose
id	Primary key
application_id	Internal application UUID
applicant_id	Applicant UUID (nullable)
field_name	Field being validated
reason_code	Standardized reason code
created_at	Timestamp

Rules:

Insert-only (no updates)

No deletes

Immutable records

This guarantees auditability and replay safety.

Logging vs Persistence
Aspect	Logs	Database
Debugging	✅	❌
Auditing	❌	✅
Analytics	❌	✅
Regulatory review	❌	✅

Validation results must never live only in logs.

API Response Behavior
Intake Endpoint (POST /v1/intake)

Returns 202 Accepted

Does not return validation details

Guarantees async processing

Callback Payload

Validation reason codes are included in:

Success callback

Partial success callback

HITL routing payloads

Testing Strategy

Validation semantics are verified through:

Unit tests

Individual validators

Rule → reason mapping

Persistence tests

Validation results are written to DB

Correct reason codes stored

Non-blocking tests

Invalid data still results in accepted intake

Transport errors are tested separately.

Design Guarantees

This system guarantees:

Intake is never blocked by dirty data

All validation issues are captured

Validation logic is extensible

New rules do not break old flows

Compliance and audit teams can reconstruct decisions

Future Extensions

Planned future uses of validation reason codes:

QA scoring (weighted confidence)

Human-in-the-Loop routing

Risk tiering

Explainability payloads

Regulatory reporting

Summary

Error semantics are not exceptions.

They are signals.

This design ensures:

Reliability under bad input

Operational clarity

Long-term regulatory safety

Clean separation of concerns