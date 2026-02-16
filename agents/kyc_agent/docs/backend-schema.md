KYC Agent — Backend Database Schema Specification
1. Purpose of This Document

This document defines:

Core database entities

Table relationships

Indexing strategy

Audit storage design

Evidence storage mapping

Versioning & replay requirements

Idempotency tracking

Compliance fields

The schema supports:

PASS / REVIEW / FAIL decisions

Multiple KYC attempts per application

Vendor response normalization

Immutable audit trail

Regulatory export capability

2. Database Philosophy

The KYC schema follows:

Relational model (PostgreSQL recommended)

ACID compliance

Append-only audit logging

Versioned attempts

Foreign-key enforced integrity

Strict immutability for final decisions

3. High-Level Entity Relationship Overview
Application
    ↓
KYC_Attempt
    ↓
----------------------------------------
| Identity_Check                      |
| Document_Check                      |
| Face_Check                          |
| AML_Check                           |
| Risk_Decision                       |
| Vendor_Response                     |
| Evidence_Artifact                   |
| Audit_Log                           |
----------------------------------------


One application may have multiple KYC attempts.

4. Core Tables
4.1 kyc_attempts

Stores each KYC execution attempt.

Fields
Column	Type	Description
id	UUID (PK)	Unique attempt ID
application_id	UUID	Reference to application
attempt_version	INT	Incremented per retry
status	ENUM	PENDING / PASSED / REVIEW / FAILED
confidence_score	FLOAT	Final aggregated score
rules_version	VARCHAR	Version of risk rules used
created_at	TIMESTAMP	Attempt start time
completed_at	TIMESTAMP	Decision time
idempotency_key	VARCHAR	Prevent duplicate execution
Indexes

Index on application_id

Unique (application_id, attempt_version)

Index on status

4.2 identity_checks

Stores identity verification results.

Column	Type
id	UUID (PK)
kyc_attempt_id	UUID (FK)
ssn_valid	BOOLEAN
ssn_plausible	BOOLEAN
name_dob_match	BOOLEAN
address_match	BOOLEAN
phone_match	BOOLEAN
email_match	BOOLEAN
identity_score	FLOAT
flags	JSONB
created_at	TIMESTAMP
4.3 document_checks

Stores document authenticity results.

Column	Type
id	UUID (PK)
kyc_attempt_id	UUID (FK)
document_type	VARCHAR
issuer_valid	BOOLEAN
expiry_valid	BOOLEAN
tamper_detected	BOOLEAN
format_valid	BOOLEAN
document_score	FLOAT
flags	JSONB
created_at	TIMESTAMP
4.4 face_checks

Stores face comparison & liveness results.

Column	Type
id	UUID (PK)
kyc_attempt_id	UUID (FK)
face_match_score	FLOAT
liveness_passed	BOOLEAN
spoof_detected	BOOLEAN
face_threshold	FLOAT
flags	JSONB
created_at	TIMESTAMP
4.5 aml_checks

Stores AML / sanctions screening.

Column	Type
id	UUID (PK)
kyc_attempt_id	UUID (FK)
ofac_match	BOOLEAN
ofac_confidence	FLOAT
pep_match	BOOLEAN
sanctions_list_version	VARCHAR
aml_score	FLOAT
flags	JSONB
created_at	TIMESTAMP
Critical Rule

If ofac_match = true → must trigger FAIL decision.

4.6 risk_decisions

Stores aggregated decision.

Column	Type
id	UUID (PK)
kyc_attempt_id	UUID (FK)
final_status	ENUM (PASS, REVIEW, FAIL)
aggregated_score	FLOAT
hard_fail_triggered	BOOLEAN
decision_reason	TEXT
decision_rules_snapshot	JSONB
model_versions	JSONB
created_at	TIMESTAMP

This table represents the official KYC outcome.

4.7 vendor_responses

Stores normalized vendor responses.

Column	Type
id	UUID (PK)
kyc_attempt_id	UUID (FK)
vendor_name	VARCHAR
vendor_service	VARCHAR
response_hash	VARCHAR
raw_response_location	VARCHAR (S3 path)
success	BOOLEAN
response_time_ms	INT
created_at	TIMESTAMP

Raw responses must not be stored directly in DB — only hashed + referenced.

4.8 evidence_artifacts

Stores evidence metadata.

Column	Type
id	UUID (PK)
kyc_attempt_id	UUID (FK)
artifact_type	ENUM (ID_IMAGE, SELFIE, VENDOR_JSON, LOG_SNAPSHOT)
storage_path	VARCHAR
file_hash	VARCHAR
encrypted	BOOLEAN
created_at	TIMESTAMP

Actual files stored in object storage.

4.9 audit_logs (Append-Only)

Stores immutable system & reviewer events.

Column	Type
id	UUID (PK)
entity_type	VARCHAR
entity_id	UUID
action	VARCHAR
actor_type	ENUM (SYSTEM, HUMAN)
actor_id	UUID (nullable)
metadata	JSONB
timestamp	TIMESTAMP

No UPDATE allowed on this table.

4.10 human_reviews

Tracks manual reviews.

Column	Type
id	UUID (PK)
kyc_attempt_id	UUID (FK)
reviewer_id	UUID
decision	ENUM (APPROVED, REJECTED, REUPLOAD_REQUESTED)
reviewer_notes	TEXT
created_at	TIMESTAMP

If reviewer approves → update risk_decisions.

5. ENUM Definitions
kyc_status_enum

PENDING

PASSED

REVIEW

FAILED

decision_enum

PASS

REVIEW

FAIL

6. Relationships

kyc_attempts → parent entity

All check tables reference kyc_attempt_id

risk_decisions has 1:1 with kyc_attempts

human_reviews optional 1:1 per review action

Foreign keys must enforce cascading restrictions (no silent deletes).

7. Versioning Strategy

Each attempt has:

attempt_version

rules_version

model_versions

Re-running KYC:

Creates new attempt_version

Preserves previous attempts

Never overwrites prior decisions

8. Idempotency Strategy

Use:

idempotency_key (unique constraint)

If same payload re-submitted:

Return previous attempt

Do not create new row

9. Indexing Strategy

Indexes required on:

application_id

kyc_attempt_id

status

ofac_match

created_at

Partial index example:

WHERE final_status = 'REVIEW'


For review queue performance.

10. Compliance Requirements in Schema

Schema must support:

Full decision replay

Vendor version traceability

Model version traceability

Threshold configuration versioning

Immutable audit trail

Regulator export capability

11. Data Retention Policy Support

Fields required for retention:

created_at

completed_at

Retention logic handled via:

Archival jobs

Legal hold flags (optional future field)

12. Security Constraints

Encrypt SSN at column level

Mask PII in logs

Use row-level security for reviewer access

Restrict direct DB access in production

Audit all read-access to evidence artifacts

13. Replay Capability

Replay requires:

Stored rules snapshot

Stored model versions

Stored vendor response hashes

Stored thresholds

Stored input payload hash

Replay must produce identical decision.

14. Shadow Mode Support

Add optional field:

shadow_decision_status

Used to compare:

Manual decision

Automated decision

No effect on production state.

15. Schema Summary Diagram (Conceptual)
kyc_attempts
    ├── identity_checks
    ├── document_checks
    ├── face_checks
    ├── aml_checks
    ├── risk_decisions
    ├── vendor_responses
    ├── evidence_artifacts
    └── human_reviews
            ↓
        audit_logs

16. Future Extensions

Optional future tables:

continuous_screening_events

identity_graph_links

device_fingerprint_history

blacklist_records

fraud_patterns

Conclusion

This backend schema ensures:

Deterministic, versioned KYC decisions

Full compliance traceability

Modular vendor integration

Immutable audit logging

Human review tracking

Idempotent execution

Replay capability

Regulatory readiness

It supports:

Phase 1 (vendor-backed KYC)

Phase 2 (hybrid ML + vendor)

Phase 3 (continuous monitoring & fraud graphing)