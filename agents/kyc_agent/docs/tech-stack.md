KYC Agent — Technical Stack Specification
1. Purpose of This Document

This document defines the complete technical stack for the KYC Agent, including:

Backend framework

Vendor integration layer

AML screening

Face match & liveness

Data storage

Security controls

Audit infrastructure

Deployment architecture

Monitoring & compliance tooling

The KYC Agent is a regulator-facing, compliance-critical service.
Technology decisions prioritize:

Determinism

Auditability

Replaceable vendor integrations

Data security

Low-latency verification

High availability

2. Architectural Overview (KYC Agent Only)
Orchestrator
     ↓
KYC API (FastAPI)
     ↓
----------------------------------
| SSN Verifier Module            |
| ID Verification Adapter        |
| Face Match Engine              |
| Liveness Engine                |
| AML / OFAC Screener            |
| Risk Aggregator                |
| Evidence Store Handler         |
----------------------------------
     ↓
Database + Object Storage


The KYC Agent is:

Stateless (application state stored externally)

Idempotent

Modular (submodules independently replaceable)

3. Backend Framework
Recommended: Python + FastAPI
Why FastAPI?

Native async support (important for vendor calls)

Automatic OpenAPI generation

High performance (ASGI-based)

Pydantic schema validation

Strong ecosystem for ML & image processing

Core Dependencies

fastapi

uvicorn

pydantic

httpx (async HTTP calls)

sqlalchemy (async)

alembic (migrations)

4. Internal KYC Modules & Technology
4.1 SSN Verifier Module
Purpose

SSN format validation

Issuance correlation

Basic fraud heuristics

Tech

Pure Python logic

Optional SSN trace vendor API

PostgreSQL validation rules

No ML required

This module must be deterministic.

4.2 ID Verification Adapter

This layer abstracts external identity vendors.

Vendor Options (Example Categories)

ID document verification APIs

Document authenticity services

OCR-based extraction vendors

Adapter Pattern
Vendor Adapter Interface
        ↓
Vendor A Adapter
Vendor B Adapter


Purpose:

Normalize vendor responses

Avoid vendor lock-in

Enable fallback provider

Tech

httpx for async calls

Pydantic for response normalization

Retry logic with exponential backoff

4.3 Face Match Engine

Two implementation options:

Option A — Vendor-Based (Recommended for Phase 1)

Use vendor’s face comparison API

Receive confidence score

Store result

Pros:

Faster to launch

Better compliance support

Option B — In-House ML Model
Stack

PyTorch / TensorFlow

Pretrained face embedding model

Cosine similarity scoring

Libraries

torch

opencv-python

face-recognition (if acceptable)

Must store:

Match score

Threshold used

Model version

4.4 Liveness Detection
Vendor-Based (Recommended)

Passive liveness API

Anti-spoof detection

Replay detection

In-House (Advanced Phase)

Depth estimation

Motion challenge verification

CNN-based spoof detection

4.5 AML / OFAC Screening
Implementation Options
Option A — Vendor AML API (Recommended)

OFAC SDN

Global sanctions lists

PEP database

Option B — In-House Screening

Requires:

Regular sanctions list ingestion

Name normalization

Fuzzy matching (Levenshtein)

False positive management

Libraries

rapidfuzz

unidecode

Must support:

Fuzzy name match scoring

Threshold configuration

Hard-stop rules for confirmed OFAC hits

4.6 Risk Aggregator
Purpose

Combine signals into:

PASS

NEEDS_HUMAN_REVIEW

FAIL

Tech

Deterministic rule engine

Config-driven thresholds

YAML-based rule configuration

Example:

rules.yaml


Advantages:

No code redeploy required for threshold tuning

Compliance visibility

Version-controlled decision logic

5. Data Storage Layer
5.1 Primary Database
PostgreSQL (Recommended)

Why:

ACID compliant

JSONB support

Reliable indexing

Strong audit compatibility

Stores:

KYC results

Confidence scores

Flags

Decision timestamps

Model versions

Vendor response hashes

5.2 Evidence Storage
S3-Compatible Object Storage

Stores:

ID images

Selfies

Vendor raw responses (encrypted)

Audit artifacts

Must have:

Server-side encryption

Versioning enabled

Access logging enabled

Time-bound pre-signed URLs

5.3 Immutable Audit Store

Options:

Append-only PostgreSQL table

WORM storage bucket

Separate audit schema

Must store:

Input hash

Output hash

Rules triggered

Actor (system/human)

Timestamp

6. Caching & Idempotency
Redis

Used for:

Idempotency keys

Request deduplication

Temporary vendor response caching

Rate limiting counters

Must enforce:

TTL expiration

Safe eviction policy

7. Messaging / Async Processing

If vendor uses async callbacks:

Options

Kafka

AWS SQS

RabbitMQ

Used for:

Vendor callback ingestion

Retry workflows

Human review triggers

8. Security Stack
8.1 Encryption

AES-256 at rest

TLS 1.2+ in transit

KMS-based key management

8.2 Secrets Management

Options:

AWS Secrets Manager

HashiCorp Vault

Kubernetes Secrets (encrypted)

8.3 Access Control

JWT authentication (validated by gateway)

Service-to-service authentication (mTLS recommended)

Role-based access control

8.4 Logging Controls

Mask SSN (show last 4 only)

No raw PII in logs

No base64 images in logs

Structured JSON logging

9. Observability & Monitoring
9.1 Logging

Structured logs (JSON)

ELK stack or equivalent

Log retention policy defined

9.2 Metrics

Use Prometheus to track:

KYC latency

Vendor response time

OFAC match rate

Review rate

Failure rate

9.3 Distributed Tracing

OpenTelemetry

Trace ID propagated from orchestrator

10. Deployment Architecture
10.1 Containerization

Docker

Multi-stage builds

Minimal base images

10.2 Orchestration

Kubernetes (recommended)

Horizontal Pod Autoscaling

Readiness + liveness probes

10.3 Scaling Strategy

Stateless service

Horizontal scaling

Vendor timeout protection

Circuit breaker implementation

11. CI/CD Pipeline

Pipeline must include:

Unit tests

Integration tests (mock vendor)

Security scanning

Dependency scanning

Docker image scanning

Schema migration automation

No production deploy without:

Audit schema validation

Rule configuration version tag

12. Performance Targets
Metric	Target
Total KYC Latency	< 8 seconds
Vendor Call Timeout	3 seconds
API P95	< 500 ms (excluding vendor wait)
Availability	99.9%
13. Compliance-Specific Technical Requirements

Decision replay capability

Model version tracking

Threshold version tracking

Vendor response hashing

Immutable audit log

Explainable decision output

14. Environment Strategy
Environment	Purpose
Dev	Feature development
QA	Integration testing
Shadow	Parallel manual verification
Staging	Pre-prod testing
Production	Live

Production must:

Use separate database

Separate encryption keys

Separate storage bucket

15. Future Enhancements (KYC-Specific)

Multi-vendor redundancy

Continuous re-screening (OFAC refresh)

Behavioral biometrics

Device fingerprint correlation

Identity graph matching

International identity expansion

16. Technology Summary Table
Component	Technology
Backend	FastAPI (Python)
Database	PostgreSQL
Cache	Redis
Object Storage	S3-compatible
Messaging	Kafka / SQS
Monitoring	Prometheus + Grafana
Logging	ELK
Containerization	Docker
Orchestration	Kubernetes
Secrets	Vault / Secrets Manager
Conclusion

The KYC Agent tech stack is designed to ensure:

Deterministic compliance decisions

Replaceable vendor integrations

Strong auditability

Secure PII handling

High scalability

Low latency

Regulatory readiness

This stack supports:

Phase 1 (vendor-backed MVP)

Phase 2 (hybrid ML + vendor)

Phase 3 (advanced fraud detection & continuous KYC)