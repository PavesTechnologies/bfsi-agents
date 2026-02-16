KYC Agent — Application Flow Specification
1. Purpose of This Document

This document defines the internal execution flow of the KYC Agent from the moment it is triggered until a final KYC decision is produced.

It covers:

Trigger conditions

Input validation

Sub-module execution order

AML screening logic

Risk aggregation

Human review escalation

Failure handling

Audit and evidence storage

Idempotency behavior

This flow is designed to ensure:

Deterministic compliance behavior

OFAC hard-stop enforcement

Explainable decision outputs

Regulator-ready audit trail

2. High-Level KYC Flow
Trigger from Orchestrator
        ↓
Input Validation & Idempotency Check
        ↓
Identity Verification
        ↓
Document Authenticity Check
        ↓
Face Match & Liveness (if applicable)
        ↓
AML / OFAC Screening
        ↓
Risk Aggregation Engine
        ↓
Decision Output (PASS / REVIEW / FAIL)
        ↓
Audit & Evidence Storage

3. Trigger Conditions

The KYC Agent is triggered when:

application_status = INTAKE_COMPLETED


The Orchestrator sends:

Structured applicant data

Document references (ID, selfie)

Metadata (IP, timestamp, device info)

KYC must not run without normalized intake data.

4. Step 1 — Idempotency & Replay Check

Before executing any logic:

Check if KYC already completed for this application_id

Validate idempotency key

If identical payload exists:

Return previous result

Do NOT re-run vendors

This prevents:

Duplicate vendor charges

Inconsistent audit records

Double decision states

5. Step 2 — Input Validation

Validate:

SSN format (9 digits)

DOB format & logical validity

Address completeness

Required fields present

Document availability

If validation fails:

kyc_status = FAIL
reason = "Invalid input data"


Failure is logged and returned immediately.

6. Step 3 — Identity Verification Flow
Sub-Checks

SSN structural validation

SSN issuance plausibility

Name–DOB–SSN consistency

Address correlation

Phone/email ownership validation

Output

Each check produces:

signal_status

confidence_score

flags[]

Example:

identity_score = 0.92
identity_flags = []


If synthetic identity signals detected → escalate to REVIEW or FAIL depending on severity.

7. Step 4 — Document Authenticity Flow

Triggered if government ID present.

Sub-Checks

Document type detection

Issuer authority validation

Expiry validation

Image tamper detection

Format compliance

Possible Outcomes
Result	Action
Valid ID	Continue
Minor anomaly	Flag for REVIEW
Fake/tampered ID	FAIL

All image analysis outputs must be stored in evidence store.

8. Step 5 — Face Match & Liveness Flow

Executed only if selfie provided.

8.1 Face Match

Extract embedding from ID photo

Extract embedding from selfie

Compute similarity score

If score < threshold:

face_flag = "LOW_CONFIDENCE"

8.2 Liveness Check

Passive liveness check OR

Motion challenge validation

Anti-spoof detection

If spoof detected:

kyc_status = FAIL
reason = "Spoofing detected"


Spoof detection is a hard failure.

9. Step 6 — AML / OFAC Screening Flow

This is the most compliance-critical step.

9.1 Screening Process

Normalize name

Fuzzy match against sanctions lists

Exact match against OFAC SDN

PEP list screening

9.2 OFAC Hard Stop Rule

If confirmed OFAC match:

kyc_status = FAIL
reason = "OFAC_MATCH"


This overrides all other signals.

No auto-override allowed.

9.3 PEP Handling

If PEP identified:

flag = "PEP_MATCH"


Escalation to REVIEW (not automatic fail).

10. Step 7 — Risk Aggregation

After all modules execute, the Risk Aggregator evaluates:

Inputs:

identity_score

document_score

face_score

aml_result

flags[]

rule configuration

10.1 Decision Logic
Hard Fail Conditions

Confirmed OFAC match

Fake/tampered ID

Spoof detection

Confirmed synthetic identity

→ FAIL

Soft Fail Conditions

Low face match

Name variations

Address mismatch

Thin-file identity

→ NEEDS_HUMAN_REVIEW

Pass Conditions

All checks valid

No sanctions hit

Confidence above threshold

→ PASS

11. Step 8 — Decision Output

The final structured output:

{
  "kyc_status": "PASS",
  "confidence_score": 0.96,
  "flags": [],
  "ofac_match": false,
  "pep_match": false,
  "model_versions": {
    "face_model": "v1.3",
    "rules_version": "2026.02"
  }
}


This is returned to the Orchestrator.

12. Human Review Flow

Triggered when:

kyc_status = NEEDS_HUMAN_REVIEW

12.1 Reviewer Receives

Trigger reason

Evidence links

Vendor results

Match scores

Flags

Rule version

12.2 Reviewer Actions
Action	Result
Approve	Convert to PASS
Reject	Convert to FAIL
Request Re-upload	Return to Intake

All reviewer actions are:

Logged

Timestamped

Immutable

13. Failure Handling Flow
Vendor Timeout

Retry (configurable attempts)

If persistent → REVIEW

Log vendor incident

Partial Failure

If non-critical module fails:

Continue with risk penalty

Escalate if threshold exceeded

System Failure

If KYC service unavailable:

Application remains in KYC_PENDING

Alert DevOps

Prevent underwriting start

14. Audit & Evidence Storage Flow

At each stage:

Hash input payload

Hash vendor responses

Store decision logic triggered

Store timestamp

Store model versions

Store confidence scores

Audit logs must support:

Replay capability

Regulatory export

Forensic investigation

15. State Transitions (KYC-Only)
Current State	Next State
KYC_PENDING	KYC_PASSED
KYC_PENDING	KYC_REVIEW
KYC_PENDING	KYC_FAILED
KYC_REVIEW	KYC_PASSED
KYC_REVIEW	KYC_FAILED

No other transitions allowed.

16. Idempotency Flow

If same payload submitted twice:

Do not re-run vendors

Return stored result

Log replay event

If payload changed:

Create new KYC attempt version

Preserve old record

17. Monitoring & Metrics Flow

KYC service must emit:

Latency per module

Vendor success rate

OFAC hit rate

Review rate

Fail rate

Average confidence score

Alert triggers:

OFAC spike

Vendor downtime

Unusual fail rate

High spoof detection rate

18. Shadow Mode Flow (Pre-Production)

In shadow mode:

KYC runs silently

Human team still verifies manually

Compare decisions

Measure false positives/negatives

Adjust thresholds

No automatic blocking in shadow mode.

19. Re-Run / Re-Verification Flow

If applicant re-uploads documents:

Increment KYC attempt version

Re-run affected modules only

Preserve previous evidence

Log version history

20. Compliance Escalation Flow

If:

Confirmed sanctions hit

Repeated fraud attempt

High-confidence synthetic identity

Then:

Lock identity record

Notify compliance team

Prevent auto re-application

Store enhanced audit log

21. SLA Targets (KYC Only)
Stage	SLA
Identity Verification	< 2 sec
Document Verification	< 3 sec
Face Match	< 2 sec
AML Screening	< 1 sec
Total KYC Flow	< 8 sec
Conclusion

The KYC Agent flow ensures:

Deterministic compliance enforcement

OFAC hard-stop guarantees

Modular execution of sub-checks

Human review buffer for ambiguity

Complete audit traceability

Idempotent execution

Vendor resilience

Regulator-ready explainability

This flow is built to withstand:

Regulatory audits

Vendor outages

Fraud attacks

Scale growth

Long-term evidence retention