# KYC Agent – Database Schema Documentation

## Overview

This document describes the database schema for the **KYC Agent microservice**.

The system is designed to support:

* Deterministic KYC decisions
* Vendor traceability
* Replay capability
* Regulatory compliance
* Human review workflows
* Idempotent API handling

The architecture follows a **modular, relational design using PostgreSQL**.

---

# Core Tables

---

## 1. `kyc_cases`

Represents a single KYC execution lifecycle.

| Column             | Type                     | Description                                                |
| ------------------ | ------------------------ | ---------------------------------------------------------- |
| id                 | UUID (PK)                | Unique identifier for the KYC case                         |
| applicant_id       | UUID                     | External reference from LOS / Orchestrator                 |
| payload_hash       | VARCHAR(64)              | SHA-256 hash of input payload for integrity & replay       |
| status             | ENUM (`kyc_status_enum`) | Current lifecycle status (PENDING, PASSED, REVIEW, FAILED) |
| confidence_score   | FLOAT                    | Final aggregated score                                     |
| rules_version      | VARCHAR(50)              | Version of decision logic applied                          |
| model_versions     | JSONB                    | Snapshot of ML models used                                 |
| threshold_snapshot | JSONB                    | Decision thresholds used                                   |
| shadow_status      | VARCHAR(50)              | Shadow decision for experimentation                        |
| created_at         | TIMESTAMP                | KYC creation timestamp                                     |
| completed_at       | TIMESTAMP                | Finalization timestamp                                     |

### Relationships

* 1:1 → IdentityCheck
* 1:1 → DocumentCheck
* 1:1 → FaceCheck
* 1:1 → AMLCheck
* 1:1 → RiskDecision
* 1:N → VendorResponse
* 1:N → EvidenceArtifact
* 1:N → HumanReview
* 1:N → KYCRequest

---

## 2. `kyc_requests`

Handles API idempotency and response replay.

| Column           | Type         | Description                      |
| ---------------- | ------------ | -------------------------------- |
| id               | UUID (PK)    | Internal request identifier      |
| idempotency_key  | VARCHAR(255) | Unique deduplication key         |
| payload_hash     | VARCHAR(64)  | Hash of original request payload |
| kyc_id           | UUID (FK)    | Associated KYC case              |
| response_payload | JSONB        | Stored API response snapshot     |
| response_status  | VARCHAR(50)  | Final response status            |
| responded_at     | TIMESTAMP    | When response was finalized      |
| created_at       | TIMESTAMP    | Request creation time            |

### Purpose

* Prevent duplicate execution
* Enable safe retries
* Ensure exactly-once semantics

---

## 3. `identity_checks`

Stores identity verification signals.

| Column         | Type      | Description                  |
| -------------- | --------- | ---------------------------- |
| id             | UUID (PK) | Identity check ID            |
| kyc_id         | UUID (FK) | Parent KYC case              |
| ssn_valid      | BOOLEAN   | SSN format validation result |
| ssn_plausible  | BOOLEAN   | Plausibility validation      |
| name_dob_match | BOOLEAN   | Name and DOB consistency     |
| address_match  | BOOLEAN   | Address verification result  |
| phone_match    | BOOLEAN   | Phone verification           |
| email_match    | BOOLEAN   | Email verification           |
| identity_score | FLOAT     | Aggregated identity score    |
| flags          | JSONB     | Structured rule flags        |
| created_at     | TIMESTAMP | Creation timestamp           |

---

## 4. `document_checks`

Stores government document verification results.

| Column          | Type      | Description                 |
| --------------- | --------- | --------------------------- |
| id              | UUID (PK) | Document check ID           |
| kyc_id          | UUID (FK) | Parent KYC case             |
| document_type   | VARCHAR   | DL / Passport etc           |
| issuer_valid    | BOOLEAN   | Issuer authenticity         |
| expiry_valid    | BOOLEAN   | Expiry validation           |
| tamper_detected | BOOLEAN   | Tamper detection            |
| format_valid    | BOOLEAN   | Format validation           |
| document_score  | FLOAT     | Document authenticity score |
| extracted_data  | JSONB     | OCR extracted fields        |
| flags           | JSONB     | Fraud indicators            |
| created_at      | TIMESTAMP | Timestamp                   |

---

## 5. `face_checks`

Biometric and liveness verification results.

| Column                 | Type      | Description             |
| ---------------------- | --------- | ----------------------- |
| id                     | UUID (PK) | Face check ID           |
| kyc_id                 | UUID (FK) | Parent KYC case         |
| face_match_score       | FLOAT     | Face similarity score   |
| liveness_passed        | BOOLEAN   | Liveness result         |
| liveness_score         | FLOAT     | Liveness confidence     |
| spoof_detected         | BOOLEAN   | Anti-spoof detection    |
| replay_attack_detected | BOOLEAN   | Replay attack detection |
| deepfake_score         | FLOAT     | Deepfake probability    |
| face_threshold         | FLOAT     | Threshold used          |
| flags                  | JSONB     | Biometric signals       |
| created_at             | TIMESTAMP | Timestamp               |

---

## 6. `aml_checks`

Sanctions and PEP screening results.

| Column                 | Type      | Description              |
| ---------------------- | --------- | ------------------------ |
| id                     | UUID (PK) | AML check ID             |
| kyc_id                 | UUID (FK) | Parent KYC case          |
| ofac_match             | BOOLEAN   | OFAC match result        |
| ofac_confidence        | FLOAT     | OFAC confidence score    |
| pep_match              | BOOLEAN   | PEP screening result     |
| aml_score              | FLOAT     | Aggregated AML score     |
| sanctions_list_version | VARCHAR   | List version             |
| matched_entity_name    | VARCHAR   | Matched sanctions entity |
| adverse_media_match    | BOOLEAN   | Negative news screening  |
| flags                  | JSONB     | AML indicators           |
| created_at             | TIMESTAMP | Timestamp                |

---

## 7. `risk_decisions`

Official KYC decision record.

| Column                  | Type                   | Description                |
| ----------------------- | ---------------------- | -------------------------- |
| id                      | UUID (PK)              | Decision ID                |
| kyc_id                  | UUID (FK)              | Parent KYC case            |
| final_status            | ENUM (`decision_enum`) | PASS / REVIEW / FAIL       |
| aggregated_score        | FLOAT                  | Final computed score       |
| hard_fail_triggered     | BOOLEAN                | Mandatory fail indicator   |
| decision_reason         | TEXT                   | Human-readable explanation |
| decision_rules_snapshot | JSONB                  | Rule snapshot              |
| threshold_snapshot      | JSONB                  | Threshold snapshot         |
| aggregated_inputs       | JSONB                  | All input scores           |
| decision_signature      | VARCHAR                | Integrity hash             |
| decision_finalized      | BOOLEAN                | Lock flag                  |
| created_at              | TIMESTAMP              | Decision time              |

---

## 8. `vendor_responses`

External vendor interaction ledger.

| Column                | Type      | Description          |
| --------------------- | --------- | -------------------- |
| id                    | UUID (PK) | Vendor response ID   |
| kyc_id                | UUID (FK) | Parent KYC case      |
| vendor_name           | VARCHAR   | Vendor provider      |
| vendor_service        | VARCHAR   | Service type         |
| vendor_version        | VARCHAR   | Vendor model version |
| response_hash         | VARCHAR   | Hash of raw response |
| raw_response_location | VARCHAR   | S3 location          |
| http_status_code      | INTEGER   | HTTP response code   |
| success               | BOOLEAN   | Call success flag    |
| response_time_ms      | INTEGER   | Execution latency    |
| error_message         | VARCHAR   | Error detail         |
| created_at            | TIMESTAMP | Timestamp            |

---

## 9. `evidence_artifacts`

Metadata for stored KYC artifacts.

| Column          | Type                        | Description                                    |
| --------------- | --------------------------- | ---------------------------------------------- |
| id              | UUID (PK)                   | Artifact ID                                    |
| kyc_id          | UUID (FK)                   | Parent KYC case                                |
| artifact_type   | ENUM (`artifact_type_enum`) | ID_IMAGE / SELFIE / VENDOR_JSON / LOG_SNAPSHOT |
| storage_path    | VARCHAR                     | Object storage path                            |
| file_hash       | VARCHAR                     | File integrity hash                            |
| mime_type       | VARCHAR                     | File content type                              |
| file_size_bytes | INTEGER                     | File size                                      |
| legal_hold      | BOOLEAN                     | Retention lock flag                            |
| encrypted       | BOOLEAN                     | Encryption status                              |
| created_at      | TIMESTAMP                   | Timestamp                                      |

---

## 10. `human_reviews`

Manual review tracking.

| Column                      | Type                                | Description                              |
| --------------------------- | ----------------------------------- | ---------------------------------------- |
| id                          | UUID (PK)                           | Review ID                                |
| kyc_id                      | UUID (FK)                           | Parent KYC case                          |
| reviewer_id                 | UUID                                | Analyst ID                               |
| reviewer_role               | VARCHAR                             | L1 / L2 / Supervisor                     |
| decision                    | ENUM (`human_review_decision_enum`) | APPROVED / REJECTED / REUPLOAD_REQUESTED |
| review_reason_codes         | JSONB                               | Structured reasons                       |
| reviewer_notes              | TEXT                                | Free text notes                          |
| overrode_automated_decision | BOOLEAN                             | Override flag                            |
| created_at                  | TIMESTAMP                           | Timestamp                                |

---

# ENUM Definitions

## `kyc_status_enum`

* PENDING
* PASSED
* REVIEW
* FAILED

## `decision_enum`

* PASS
* REVIEW
* FAIL

## `human_review_decision_enum`

* APPROVED
* REJECTED
* REUPLOAD_REQUESTED

## `artifact_type_enum`

* ID_IMAGE
* SELFIE
* VENDOR_JSON
* LOG_SNAPSHOT

---

# Relationship Summary

* `kyc_cases` is the parent entity.
* Sub-check tables (identity, document, face, aml, risk_decision) are **1:1 relationships**.
* Vendor responses, artifacts, human reviews, and requests are **1:N relationships**.
* All foreign keys use `CASCADE` delete.
* Final decisions are immutable once finalized.

---

# Compliance & Replay

The schema supports:

* Deterministic replay
* Model version traceability
* Threshold snapshot preservation
* Audit-grade evidence storage
* Idempotent API handling

This design ensures **regulatory readiness and scalable KYC orchestration**.
