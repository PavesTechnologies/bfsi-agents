# Product Requirements Document (PRD)
## Project: Intake Processing & Verification Platform
## Version: 1.0
## Owner: Platform Engineering
## Status: Draft (Implementation-Ready)

---

## 1. Purpose

Build a production-grade intake service that ingests identity and document data, validates and processes it asynchronously, enriches it, scores quality, ensures compliance, and produces auditable, deterministic outputs with callback-based delivery.

The system must be:
- Highly reliable
- Auditable
- Idempotent
- Secure
- Horizontally scalable
- Compliance-ready

---

## 2. Goals

### Primary Goals
1. Provide a stable API for identity/document intake.
2. Ensure asynchronous, non-blocking processing.
3. Guarantee idempotent behavior.
4. Maintain immutable audit records.
5. Support document + OCR-based extraction.
6. Produce standardized outputs with confidence scoring.
7. Enable human review workflows.
8. Meet compliance and security standards.

### Non-Goals
- Real production ML model deployment (mocked initially).
- Real external enrichment providers (mocked).
- Real-time processing (batch async only).

---

## 3. Target Users

| Role | Usage |
|------|--------|
| API Clients | Submit intake requests |
| Compliance Team | Audit and review records |
| Operations | Monitor health and failures |
| QA Analysts | Review HITL cases |

---

## 4. System Overview

### High-Level Flow

1. Client submits intake request  
2. API validates + audits request  
3. Job is enqueued asynchronously  
4. Processing pipeline executes  
5. Entities extracted and normalized  
6. Enrichment + QA scoring  
7. HITL routing (if needed)  
8. Output assembled  
9. Callback delivered  
10. Data persisted  

---

## 5. Architecture

### Core Components

| Component | Responsibility |
|-----------|----------------|
| FastAPI Service | API layer |
| Async Executor | Background jobs |
| Persistence Layer | Postgres |
| Object Storage | Documents |
| OCR Engine | Text extraction |
| Callback Engine | Webhooks |
| Audit Store | Immutable logs |

### Deployment
- Containerized via Docker  
- Single service initially  
- Future microservice split supported  

---

## 6. Functional Requirements

---

## 6.1 Service & Infrastructure

### Requirements

| ID | Requirement |
|----|-------------|
| INF-1 | Standard agent repository |
| INF-2 | FastAPI bootstrap |
| INF-3 | Fail-fast config loader |
| INF-4 | Structured JSON logging |
| INF-5 | Base exception hierarchy |
| INF-6 | Dockerized deployment |
| INF-7 | Health endpoints |

### Health Endpoints

| Endpoint | Behavior |
|----------|----------|
| /health/live | Process alive |
| /health/ready | DB + dependencies |

---

## 6.2 Async Execution

### Requirements

| ID | Requirement |
|----|-------------|
| ASY-1 | enqueue(job) interface |
| ASY-2 | In-process executor |
| ASY-3 | 202 immediate response |
| ASY-4 | Lifecycle logging |

### States

```
QUEUED → STARTED → COMPLETED → FAILED
```

All transitions must be persisted.

---

## 6.3 API Contract

### Endpoint

```
POST /v1/intake
```

### Required Fields

| Field | Type | Required |
|-------|------|----------|
| request_id | UUID | Yes |
| callback_url | URL | Yes |
| payload | Object | Yes |

### Behavior
- Missing fields → 400  
- Accepted → 202  
- Duplicate → cached response  

---

## 6.4 Idempotency

### Requirements

| ID | Requirement |
|----|-------------|
| IDE-1 | Unique constraint on request_id |
| IDE-2 | Duplicate detection |
| IDE-3 | Cached replay |
| IDE-4 | Unit tests |

### Storage

```
idempotency (
  request_id PK,
  response_payload,
  created_at
)
```

---

## 6.5 Audit Logging

### Requirements

| ID | Requirement |
|----|-------------|
| AUD-1 | Immutable table |
| AUD-2 | Encrypted payload |
| AUD-3 | Payload hash |
| AUD-4 | Log masking |
| AUD-5 | Fail-on-write-failure |

### Guarantees
- Insert-only  
- No update/delete  
- Append-only indexes  

---

## 6.6 Callback System

### Requirements

| ID | Requirement |
|----|-------------|
| CB-1 | Standard schema |
| CB-2 | Retry-safe delivery |
| CB-3 | Exactly-once |
| CB-4 | Success/failure support |

### Callback Payload

```json
{
  "request_id": "",
  "status": "SUCCESS|FAILED|PARTIAL",
  "result": {},
  "errors": [],
  "timestamp": ""
}
```

---

## 6.7 Typed Field Intake

### Fields

| Field | Validation |
|-------|------------|
| SSN | Regex |
| DOB | Age ≥ 18 |
| Phone | E.164 |
| Email | RFC |

### Behavior
- Invalid fields flagged  
- Intake not blocked  
- Validation result stored  

---

## 6.8 Error Semantics

### Requirements

| ID | Requirement |
|----|-------------|
| ERR-1 | Standard reason codes |
| ERR-2 | Rule → Code mapping |
| ERR-3 | Persisted |

### Example

```
DOB_UNDER_18
INVALID_SSN_FORMAT
EMAIL_DOMAIN_RISK
```

---

## 6.9 Document Intake

### Endpoint

```
POST /v1/intake/documents
```

### Behavior
- Multipart upload  
- MIME validation  
- Temp storage  
- Metadata persistence  

---

## 6.10 Metadata Capture

### Sources

| Field | Source |
|-------|--------|
| IP | Headers |
| Browser | UA |
| Device | UA |
| Region | IP |

Stored in `intake_context`.

---

## 6.11 Document Type Identification

### Types

| Type |
|------|
| Passport |
| DL |
| W-2 |
| Paystub |
| Other |

### Output

```
{
  type,
  confidence
}
```

---

## 6.12 Image Preprocessing

### Pipeline

1. Deskew  
2. Denoise  
3. Enhance contrast  
4. Quality scoring  

Low quality flagged.

---

## 6.13 OCR

### Supported

| Document | Method |
|----------|--------|
| DL | PDF417 |
| Passport | MRZ |
| Paystub | OCR |
| W-2 | OCR |

### Output
Raw text blocks + coordinates.

---

## 6.14 Entity Extraction

### Entities

| Type |
|------|
| Name |
| DOB |
| Address |
| Employer |
| Income |

Each includes confidence score.

---

## 6.15 Normalization

### Rules

| Type | Rule |
|------|------|
| Name | Uppercase, strip punctuation |
| Address | USPS expansion |
| ZIP | Format check |

---

## 6.16 Cross-Source Consistency

### Checks

| Check |
|-------|
| Name mismatch |
| Address mismatch |
| Employer mismatch |

Results persisted.

---

## 6.17 Enrichment (Mock)

### Providers

| Provider | Output |
|----------|--------|
| USPS | ZIP+4 |
| Employer | NAICS |
| Phone | Risk |
| Email | Domain risk |

All mocked initially.

---

## 6.18 Compliance

### Requirements

| ID | Requirement |
|----|-------------|
| COM-1 | Optional demographics |
| COM-2 | Immutable raw data |
| COM-3 | Data versioning |
| COM-4 | PII encryption |
| COM-5 | Secret management |
| COM-6 | RBAC |

---

## 6.19 QA Scoring

### Model

```
QA Score = Σ(weight_i × confidence_i)
```

Config-driven thresholds.

---

## 6.20 Human-in-the-Loop (HITL)

### Routing Rules

| Condition | Action |
|-----------|---------|
| Low QA | Route |
| Mismatch | Route |
| OCR fail | Route |

Includes explanation payload.

---

## 6.21 Final Output

### Output Format
- Canonical JSON  
- Sorted keys  
- Schema validated  

### Includes

| Field |
|-------|
| Entities |
| Scores |
| Evidence paths |
| Metadata |
| Version |

---

## 6.22 System Exit Tests

### Required

| Test |
|------|
| Happy path |
| Failure path |
| Audit replay |
| Compliance readiness |

All must pass for release.

---

## 7. Non-Functional Requirements

---

## 7.1 Performance

| Metric | Target |
|--------|---------|
| API latency | < 100ms |
| Job enqueue | < 50ms |
| Callback delivery | < 5s |

---

## 7.2 Reliability

| Metric | Target |
|--------|---------|
| Availability | 99.9% |
| Job loss | 0% |
| Audit loss | 0% |

---

## 7.3 Security

- AES-256 at rest  
- TLS 1.3  
- HSM/KMS  
- Secrets vault  
- RBAC  
- IP allowlist  

---

## 7.4 Observability

### Required
- Structured logs  
- Correlation IDs  
- Prometheus metrics  
- Traces  
- Alerting  

---

## 8. Data Model (Core Tables)

### intake_request

```
id
request_id
status
payload_enc
created_at
```

### audit_log

```
id
request_id
payload_hash
payload_enc
created_at
```

### async_jobs

```
job_id
request_id
state
started_at
ended_at
```

### entities

```
id
request_id
type
value
confidence
```

---

## 9. Acceptance Criteria

### API
- [ ] Reject missing fields  
- [ ] Enforce idempotency  
- [ ] Return 202  

### Processing
- [ ] All jobs complete or fail deterministically  
- [ ] All states persisted  

### Audit
- [ ] Insert-only verified  
- [ ] Replay supported  

### Compliance
- [ ] Encryption verified  
- [ ] Version history present  

### QA
- [ ] Scores computed  
- [ ] Thresholds configurable  

### Callbacks
- [ ] Exactly-once delivery  
- [ ] Retry-safe  

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| In-process executor failure | Future queue migration |
| OCR accuracy | Manual review |
| Data breach | Encryption + RBAC |
| Callback loss | Persistent delivery queue |

---

## 11. Roadmap

### Phase 1 (MVP)
- API  
- Async executor  
- Audit  
- Idempotency  
- Basic OCR  
- Mock enrichment  

### Phase 2
- HITL  
- Advanced normalization  
- Scaling  
- External providers  

### Phase 3
- ML classifiers  
- Distributed workers  
- Multi-region  

---

## 12. Open Questions

1. Will this move to distributed queue (Kafka/SQS)?  
2. Required regulatory certifications (SOC2, ISO)?  
3. SLA guarantees?  
4. External provider contracts?  

---
