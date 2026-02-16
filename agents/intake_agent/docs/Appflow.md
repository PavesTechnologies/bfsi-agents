# Application Flow Document
## Project: Intake Processing & Verification Platform
## Version: 1.0
## Status: Draft (Implementation-Ready)

---

## 1. Purpose

This document defines the end-to-end application flow for the Intake Processing & Verification Platform, from API request ingestion to final output delivery and auditing.

It serves as the operational blueprint for developers, QA, and platform engineers.

---

## 2. High-Level System Flow

```
Client
   ↓
API Gateway / FastAPI
   ↓
Validation + Audit
   ↓
Async Job Queue
   ↓
Processing Pipeline
   ↓
Scoring + HITL
   ↓
Output Assembly
   ↓
Callback Delivery
   ↓
Persistence + Audit
```

---

## 3. Entry Flow (API Intake)

### 3.1 Request Submission

1. Client sends `POST /v1/intake`
2. Request includes:
   - request_id
   - callback_url
   - payload
   - headers

---

### 3.2 API Layer Processing

```
Receive Request
   ↓
Generate/Validate request_id
   ↓
Validate Schema (Pydantic)
   ↓
Validate Required Fields
   ↓
Extract Metadata
   ↓
Idempotency Check
```

---

### 3.3 Idempotency Handling

#### If request_id exists:
```
Fetch Cached Response
   ↓
Return 200/202
   ↓
Stop Processing
```

#### If request_id is new:
```
Continue Processing
```

---

### 3.4 Audit Logging (Pre-Processing)

```
Encrypt Payload
   ↓
Generate Hash
   ↓
Insert Audit Record
   ↓
If Fail → Reject Request
```

---

### 3.5 Job Enqueue

```
Create Job Record
   ↓
Persist Job State = QUEUED
   ↓
Submit to Executor
   ↓
Return 202
```

---

## 4. Async Processing Flow

### 4.1 Job Startup

```
Executor Picks Job
   ↓
Update State = STARTED
   ↓
Start Trace Context
```

---

### 4.2 Processing Pipeline

```
Load Intake Context
   ↓
Document Processing (Optional)
   ↓
OCR
   ↓
Entity Extraction
   ↓
Normalization
   ↓
Cross-Source Validation
   ↓
Enrichment
   ↓
QA Scoring
```

Each stage logs:
- Start time
- End time
- Errors
- Outputs

---

## 5. Document Processing Flow

### 5.1 Upload

```
POST /v1/intake/documents
   ↓
Validate MIME
   ↓
Store Temp File
   ↓
Save Metadata
```

---

### 5.2 Classification

```
Load File
   ↓
Rule-Based Classifier
   ↓
ML Interface (Mock)
   ↓
Return Type + Confidence
```

---

### 5.3 Image Preprocessing

```
Deskew
   ↓
Denoise
   ↓
Enhance
   ↓
Quality Check
```

Low quality → Flag.

---

### 5.4 OCR Extraction

```
Identify Document Type
   ↓
Apply Parser/OCR
   ↓
Extract Raw Text
   ↓
Map Coordinates
```

---

## 6. Validation & Normalization Flow

### 6.1 Field Validation

```
Iterate Fields
   ↓
Apply Regex Rules
   ↓
Apply Business Rules
   ↓
Generate Validation Result
```

Invalid fields are flagged, not blocked.

---

### 6.2 Normalization

```
Normalize Name
   ↓
Normalize Address
   ↓
Normalize ZIP
   ↓
Split Components
```

---

## 7. Entity Extraction Flow

```
Load OCR/Text
   ↓
Pattern Matching
   ↓
NER Rules
   ↓
Confidence Assignment
   ↓
Persist Entities
```

---

## 8. Cross-Source Consistency Flow

```
Compare Source A vs B
   ↓
Detect Mismatch
   ↓
Generate Flags
   ↓
Persist Results
```

---

## 9. Enrichment Flow (Mocked)

```
Prepare Normalized Data
   ↓
Call Mock Adapters
   ↓
Receive Results
   ↓
Map to Schema
```

Adapters:
- USPS
- Employer
- Phone
- Email

---

## 10. QA Scoring Flow

```
Load Entities
   ↓
Load Config Weights
   ↓
Compute Score
   ↓
Apply Thresholds
```

---

## 11. HITL (Human-in-the-Loop) Flow

### 11.1 Routing Decision

```
Check QA Score
   ↓
Check Mismatch Flags
   ↓
Check OCR Quality
```

---

### 11.2 Routing

#### If HITL Required:
```
Generate Explanation
   ↓
Attach Reason Codes
   ↓
Create Review Task
   ↓
Pause Automation
```

#### Else:
```
Continue Automation
```

---

## 12. Output Assembly Flow

```
Collect All Results
   ↓
Link Evidence
   ↓
Generate Canonical JSON
   ↓
Sort Keys
   ↓
Validate Schema
```

---

### Output Includes
- Entities
- Confidence Scores
- Validation Results
- Evidence Paths
- Metadata
- Version Info

---

## 13. Callback Delivery Flow

### 13.1 Preparation

```
Build Payload
   ↓
Sign/Hash (Optional)
   ↓
Persist Callback Record
```

---

### 13.2 Delivery

```
POST to callback_url
   ↓
Wait Response
```

---

### 13.3 Handling

#### Success:
```
Mark Delivered
```

#### Failure:
```
Retry (Backoff)
   ↓
Max Retries → Dead Letter
```

---

## 14. Error Handling Flow

### 14.1 Validation Errors (Sync)

```
Detect Error
   ↓
Return 400
   ↓
Log
```

---

### 14.2 Processing Errors (Async)

```
Catch Exception
   ↓
Map Reason Code
   ↓
Persist Failure
   ↓
Send Failure Callback
```

---

### 14.3 System Errors

```
Detect Infrastructure Failure
   ↓
Mark Job Failed
   ↓
Alert Ops
   ↓
Retry (If Safe)
```

---

## 15. Audit & Persistence Flow

### 15.1 Audit Trail

```
Every Stage
   ↓
Append Audit Record
   ↓
Hash Verify
```

Insert-only guarantee.

---

### 15.2 Data Versioning

```
New Processing Run
   ↓
Create New Version
   ↓
Link Previous
```

---

## 16. Completion Flow

### 16.1 Success Path

```
Job Completed
   ↓
Update State = COMPLETED
   ↓
Send Callback
   ↓
Archive Temp Files
```

---

### 16.2 Partial Success Path

```
Some Fields Failed
   ↓
Mark Partial
   ↓
Send Partial Callback
   ↓
Flag for Review
```

---

### 16.3 Failure Path

```
Critical Error
   ↓
State = FAILED
   ↓
Send Failure Callback
   ↓
Persist Evidence
```

---

## 17. Health & Monitoring Flow

### 17.1 Liveness

```
Ping Service
   ↓
Return 200
```

---

### 17.2 Readiness

```
Check DB
   ↓
Check Storage
   ↓
Check Queue
   ↓
Return Status
```

---

## 18. End-to-End Flow Summary

```
API Intake
   ↓
Audit + Validate
   ↓
Enqueue
   ↓
Process
   ↓
Extract
   ↓
Normalize
   ↓
Enrich
   ↓
Score
   ↓
HITL (Optional)
   ↓
Assemble Output
   ↓
Callback
   ↓
Archive + Audit
```

---

## 19. Exit Criteria

The application flow is considered complete when:

- All stages are traceable
- All states are persisted
- All failures are recoverable
- All outputs are deterministic
- All audits are replayable
- All callbacks are reliable

---

## 20. Open Issues

1. Transition to distributed queue?
2. HITL tooling UI?
3. Real provider integration timeline?
4. Disaster recovery automation?

---
