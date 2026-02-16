KYC / Identity Agent — Domain & Implementation Documentation 

1. Purpose of the KYC Agent  

The KYC Agent is responsible for answering one fundamental question: 

“Is this applicant a real, legitimate, non-sanctioned individual, and can we legally do business with them?” 

This agent: 

Protects the bank from identity fraud, synthetic identity fraud, and regulatory violations 

Acts as a legal gatekeeper before credit, underwriting, or disbursement 

Produces audit-ready identity proof required by regulators 

It is not optional, not best-effort, and not probabilistic-only. 
Its outputs directly impact BSA/AML, OFAC, ECOA, and FCRA obligations. 

 

2. Regulatory & Compliance Scope  

The KYC Agent must explicitly satisfy: 

Mandatory Regulations 

BSA / AML – identity verification & suspicious activity detection 

OFAC – sanctions screening 

PEP (Politically Exposed Persons) checks 

CIP (Customer Identification Program) requirements 

GLBA – data protection 

ECOA / Reg B – no discriminatory behavior 

FCRA – accuracy, explainability, and dispute handling 

 
Any KYC decision must be explainable, replayable, and auditable years later. 

 

3. Inputs to the KYC Agent 

The KYC Agent is triggered after Intake Agent normalization. 

Structured Inputs 

From LOS / Orchestrator: 

{ 
  "applicant_id": "...", 
  "full_name": "...", 
  "dob": "...", 
  "ssn": "...", 
  "address": { 
    "line1": "...", 
    "city": "...", 
    "state": "...", 
    "zip": "..." 
  }, 
  "phone": "...", 
  "email": "..." 
} 
 

Document Inputs 

From Document Store (S3-compatible): 

Government ID (DL / Passport) 

Selfie or live capture (optional but recommended) 

Metadata: device, IP, submission timestamp 

 

4. Core Responsibilities  

4.1 Identity Verification  

SSN validation (format, issuance year, state correlation) 

Name–DOB–SSN consistency 

Address history correlation 

Phone & email ownership checks 

4.2 Document Authenticity  

ID document type detection 

Issuing authority validation (state/federal) 

Tamper detection (image forensics) 

Expiry and format validation 

4.3 Liveness & Presence  

Selfie vs ID face match 

Liveness challenge (blink / motion / depth) 

Replay / deepfake resistance 

4.4 AML / Sanctions Screening  

OFAC SDN list screening 

Global sanctions lists 

PEP identification 

Negative media flags (where allowed) 

 

5. Internal Logical Architecture 

5.1 Sub-Modules Inside the KYC Agent 

The KYC Agent is not one model. It is a composed agent: 

Sub-Module 

Responsibility 

SSN Verifier 

SSN trace & correlation 

ID Analyzer 

Document authenticity 

Face Match Engine 

Selfie ↔ ID match 

Liveness Engine 

Anti-spoofing 

AML Screener 

OFAC / PEP 

Risk Aggregator 

Final KYC decision 

Evidence Store 

Audit artifacts 

Each sub-module must be independently replaceable. 

 

6. Decision Model (How Final KYC Status Is Determined) 

6.1 KYC Is NOT Binary 

Final output is one of: 

PASS 

️ NEEDS_HUMAN_REVIEW 

 FAIL 

6.2 Example Decision Logic 

Signal 

Result 

SSN valid + ID valid + Face match + No OFAC 

PASS 

Minor mismatch / low confidence 

NEEDS_HUMAN_REVIEW 

OFAC hit / fake ID / synthetic signals 

FAIL 

OFAC hit is a hard stop. No auto-override. 

 

7. Outputs of the KYC Agent 

7.1 Structured Output (to LOS & Orchestrator) 

{ 
  "kyc_status": "PASS", 
  "confidence_score": 0.96, 
  "flags": [], 
  "ofac_match": false, 
  "pep_match": false, 
  "vendor_results": { 
    "id_verification": "success", 
    "liveness": "success" 
  } 
} 
 

7.2 Audit & Evidence Artifacts  

Stored immutably: 

Vendor responses (hashed) 

Image match scores 

Model versions 

Decision rules triggered 

Timestamped inputs & outputs 

 

8. Failure, Escalation & Human-in-Loop 

When Human Review Is Triggered 

Name variations (Jr / Sr / initials) 

Address mismatch across sources 

Low confidence face match 

Thin-file identity 

Human UI Payload 

{ 
  "reason": "Low face match confidence", 
  "evidence_links": ["s3://..."], 
  "recommended_action": "Request re-upload" 
} 
 

 

9. Security & Data Handling Rules 

All PII encrypted at rest & transit 

No raw images in logs 

Time-bound access tokens 

Role-based access  

Retention aligned with GLBA & bank policy 

 

Implementation Plan  

Phase 1 — Design & Contracts  

Finalize KYC API contract 

Define KYC status schema 

Identify pilot KYC vendor 

Define audit schema & evidence storage 

Deliverables: 

OpenAPI spec 

Decision matrix 

Compliance sign-off draft 

 

Phase 2 — Vendor Integration  

Integrate 1 identity vendor (ID verification + OFAC) 

Implement async callback handling 

Normalize vendor responses into internal schema 

Deliverables: 

Vendor adapter 

Mock failure scenarios 

Retry & timeout logic 

 

Phase 3 — Agent Core Logic  

Build Risk Aggregator 

Implement rule engine (hard vs soft fails) 

Store explainability artifacts 

Implement idempotency 

Deliverables: 

KYC Agent microservice 

Evidence storage pipeline 

Unit + integration tests 

 

Phase 4 — Human-in-Loop & Shadow Mode  

Integrate HumanUI escalation 

Run shadow KYC alongside manual process 

Measure false positives / false negatives 

Deliverables: 

Shadow mode metrics 

Reviewer feedback loop 

 

Phase 5 — Production Rollout  

Enable auto-PASS for low-risk 

Keep FAIL + REVIEW gated 

Enable monitoring & alerts 

Deliverables: 

Production dashboards 

Runbook 

Rollback plan 

 

10. KPIs for the KYC Agent 

KYC pass rate 

False positive rate 

Human review rate 

Average KYC decision time 

OFAC false positives 

Audit completeness score 

 