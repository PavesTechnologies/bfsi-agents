# BFSI-Agents Project Database Schema

This document provides a comprehensive overview of the database schema used across the Loan Origination System (LOS). All agents share a unified Aiven Postgres database.

## 1. System & Infrastructure Tables

### `node_audit_logs`
Centralized table for tracking LangGraph node executions across all agents.
- **id**: UUID (Primary Key)
- **application_id**: String(50) (Relation to the process instance)
- **agent_name**: String(50) (e.g., 'intake_agent', 'kyc_agent')
- **node_name**: String(100)
- **input_state**: JSONB (Snapshot of step input)
- **output_state**: JSONB (Snapshot of step output)
- **status**: String(20) (SUCCESS, FAILED)
- **error_message**: Text
- **execution_time_ms**: Integer
- **created_at**: DateTime (Timezone aware)

### `audit_logs`
Generic table for data-level audit trails (CRUD operations).
- **id**: Integer (Primary Key)
- **action**: String(20) (INSERT, UPDATE, DELETE)
- **table_name**: String(50)
- **record_id**: JSONB
- **old_data**: JSONB
- **new_data**: JSONB
- **created_at**: DateTime

### `intake_idempotency`
Prevents duplicate processing of intake requests.
- **request_id**: UUID (Primary Key)
- **app_id**: UUID
- **request_hash**: String(64)
- **status**: String(32)
- **response_payload**: JSON
- **updated_at**: DateTime

---

## 2. Intake Agent (Core Loan Application)

### `loan_application`
The master record for a loan request.
- **application_id**: UUID (Primary Key)
- **loan_type**: String(50)
- **credit_type**: String(20)
- **loan_purpose**: String(50)
- **requested_amount**: Numeric(12, 2)
- **requested_term_months**: Integer
- **application_status**: Enum (SUBMITTED, PENDING, APPROVED, DECLINED, etc.)
- **created_at**: DateTime

### `applicant`
Personal information for primary and co-applicants.
- **applicant_id**: UUID (Primary Key)
- **application_id**: UUID (Foreign Key to `loan_application`)
- **first_name**: String(100)
- **last_name**: String(100)
- **email**: String (Unique)
- **phone_number**: Text
- **ssn_encrypted**: Text
- **date_of_birth**: Date
- **gender**: Enum
- **applicant_role**: String(20) (primary, co_applicant)

### `address`
Applicant residential history.
- **address_id**: UUID (Primary Key)
- **applicant_id**: UUID (Foreign Key to `applicant`)
- **address_line1**: String(255)
- **city**: String(100)
- **state**: String(30)
- **zip_code**: String(10)
- **housing_status**: String(30) (own, rent)
- **monthly_housing_payment**: Numeric(10, 2)

### `pgsqldocument`
Binary storage for uploaded application documents.
- **id**: UUID (Primary Key)
- **application_id**: UUID (Foreign Key to `loan_application`)
- **document_type**: String(50)
- **file_name**: String
- **content**: LargeBinary (File bytes)
- **mime_type**: String(100)
- **is_low_quality**: Boolean

---

## 3. KYC Agent (Validation & Risk)

### `kyc_cases`
Orchestration record for the KYC process for an applicant.
- **id**: UUID (Primary Key)
- **applicant_id**: UUID (Foreign Key to `applicant`)
- **status**: Enum (PENDING, COMPLETED, FAILED)
- **confidence_score**: Float
- **created_at**: DateTime

### `identity_checks`
Aggregated identity verification results.
- **id**: UUID (Primary Key)
- **kyc_id**: UUID (Foreign Key to `kyc_cases`)
- **final_status**: String
- **ssn_valid**: Boolean
- **deceased_flag**: Boolean

### `document_checks`
OCR and verification results for physical documents.
- **id**: UUID (Primary Key)
- **kyc_id**: UUID (Foreign Key to `kyc_cases`)
- **document_type**: String(100)
- **issuer_valid**: Boolean
- **expiry_valid**: Boolean
- **tamper_detected**: Boolean

### `face_checks`
Biometric verification results.
- **id**: UUID (Primary Key)
- **kyc_id**: UUID (Foreign Key to `kyc_cases`)
- **face_match_score**: Float
- **liveness_passed**: Boolean
- **spoof_detected**: Boolean

### `risk_decisions`
Final KYC-level risk aggregator.
- **id**: UUID (Primary Key)
- **kyc_id**: UUID (Foreign Key to `kyc_cases`)
- **final_status**: Enum (PASS, FAIL, MANUAL_REVIEW)
- **aggregated_score**: Float
- **decision_reason**: Text

---

## 4. Decisioning & Disbursement Agent Returns

### `underwriting_decisions`
Persistent outcomes from the Decisioning Agent.
- **id**: UUID (Primary Key)
- **application_id**: String(50) (Unique ID for lookup)
- **correlation_id**: String(100) (Upstream trace identifier propagated from request lineage)
- **decision**: String(20) (APPROVE, DECLINE, COUNTER_OFFER)
- **risk_tier**: String(10)
- **risk_score**: Float
- **approved_amount**: Numeric(12, 2)
- **interest_rate**: Float
- **tenure_months**: Integer
- **explanation**: Text
- **reasoning_steps**: JSONB (Snapshot of LLM reasoning)

### `underwriting_idempotency`
Replay protection for the Decisioning Agent keyed by the intake `application_id`.
- **application_id**: String(50) (Primary Key)
- **request_hash**: String(64)
- **status**: String(32)
- **response_payload**: JSONB
- **error_message**: Text
- **updated_at**: DateTime

### `disbursement_records`
Persistent records of loan fund transfers.
- **id**: UUID (Primary Key)
- **application_id**: String(50)
- **correlation_id**: String(100) (Upstream trace identifier propagated from request lineage)
- **transaction_id**: String(100)
- **status**: String(20) (INITIATED, COMPLETED, FAILED)
- **disbursement_amount**: Numeric(12, 2)
- **monthly_emi**: Numeric(12, 2)
- **repayment_schedule**: JSONB (Full schedule)
- **transfer_timestamp**: DateTime

### `disbursement_idempotency`
Replay protection for the Disbursement Agent keyed by the intake `application_id`.
- **application_id**: String(50) (Primary Key)
- **request_hash**: String(64)
- **status**: String(32)
- **response_payload**: JSONB
- **error_message**: Text
- **updated_at**: DateTime

### `disbursement_transition_logs`
Persistent lifecycle transitions for the Disbursement Agent state machine.
- **id**: UUID (Primary Key)
- **application_id**: String(50)
- **correlation_id**: String(100)
- **from_status**: String(32)
- **to_status**: String(32)
- **reason**: Text
- **transition_metadata**: JSONB
- **created_at**: DateTime

### `service_audit_logs`
Service-level execution audit records for non-node operations in Decisioning and Disbursement.
- **id**: UUID (Primary Key)
- **application_id**: String(50)
- **correlation_id**: String(100)
- **agent_name**: String(50)
- **operation_name**: String(100)
- **request_payload**: JSONB
- **response_payload**: JSONB
- **status**: String(20)
- **error_message**: Text
- **execution_time_ms**: Integer
- **created_at**: DateTime
