# Sprint Task Breakdown — BFSI India

## Sprint 1: Intake Agent India (2 Weeks)

### Week 1: Data Models + Validators

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 1.1 | Migrate `Applicant` model: remove SSN/ITIN, add Aadhaar/PAN/CKYC fields | 3 | — | Alembic migration runs, columns exist in DB |
| 1.2 | Migrate `Address` model: ZIP→PIN, add district, default country=INDIA | 2 | — | Migration runs, constraints valid |
| 1.3 | Update `PgsqlDocument` check constraint for Indian doc types | 2 | — | DB accepts all 14 Indian doc types |
| 1.4 | Rewrite `constants.py`: Indian regexes, state codes, Devanagari name support | 3 | — | Unit tests pass for all regex patterns |
| 1.5 | Rewrite `typed_field_validators.py`: Aadhaar, PAN, PIN code, IFSC, +91 phone | 5 | 1.4 | 100% test coverage on validators |
| 1.6 | Update `reason_codes.py` with Indian-specific codes | 1 | — | All codes have unique identifiers |

### Week 2: Document Validation + OCR + ZIP Upload

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 1.7 | Create `aadhaar_validation.py` (Verhoeff + keywords + QR) | 5 | 1.4 | Validates real Aadhaar format, rejects invalid checksums |
| 1.8 | Create `pan_validation.py` (regex + entity type) | 3 | 1.4 | Validates all PAN entity types (P,C,H,F,T) |
| 1.9 | Create `voter_id_validation.py` (EPIC format) | 2 | — | Validates EPIC format `[A-Z]{3}[0-9]{7}` |
| 1.10 | Create `india_driving_license_validation.py` | 3 | — | Validates state-prefix DL format |
| 1.11 | Create `multilingual_ocr.py` (Google Vision + Tesseract + Bhashini) | 8 | — | Hindi doc OCR accuracy > 85%, engine switching works |
| 1.12 | Create `hindi_postprocessor.py` | 3 | 1.11 | Common Devanagari OCR errors corrected |
| 1.13 | Create `zip_processor.py` + API endpoint | 5 | 1.7-1.10 | ZIP upload → extract → classify → validate → store pipeline works end-to-end |
| 1.14 | Update doc classification rules for Indian docs | 3 | — | Classifier correctly identifies all Indian doc types |
| 1.15 | Delete USA-specific files (SSN, AAMVA DL, normalizers) | 1 | — | No USA-specific code remains |

**Sprint 1 Total: 49 points**

---

## Sprint 2: KYC Agent India (2 Weeks)

### Week 1: Core KYC Nodes

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 2.1 | Create `AadhaarVerification` + `PANVerification` DB models | 3 | — | Migrations run, FK to kyc_cases |
| 2.2 | Create `uidai_ekyc_service.py` (UIDAI OTP eKYC client) | 5 | — | Mock adapter works; real API integration tested |
| 2.3 | Create `pan_verification_service.py` (NSDL API client) | 3 | — | Verifies PAN + name + DOB match |
| 2.4 | Create `aadhaar_pan_node.py` (replaces SSN node) | 5 | 2.2, 2.3 | Verifies Aadhaar + PAN + linkage check |
| 2.5 | Modify `address_node.py` for India (Aadhaar address / India Post) | 3 | 2.2 | Address from eKYC compared with submitted address |
| 2.6 | Modify `aml_node.py` (RBI sanctions + UNSC watchlists) | 3 | — | Screens against Indian AML lists |
| 2.7 | Modify `contact_node.py` (+91, Indian MX domains) | 2 | — | Validates Indian phone + email correctly |
| 2.8 | Create mock adapters (CIBIL, UIDAI, NSDL) | 3 | — | All mocks return realistic Indian data |

### Week 2: Video KYC + Face Dedup + Encryption

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 2.9 | Create `VideoKYCSession` DB model | 2 | — | Stores session ID, video URL, geo-tag, audit hash |
| 2.10 | Create `video_kyc_service.py` (V-CIP provider integration) | 8 | — | Session create/poll/result lifecycle works |
| 2.11 | Create `video_kyc_node.py` | 3 | 2.10 | Node initiates V-CIP, waits for result, validates liveness |
| 2.12 | Create `face_dedup_service.py` (embedding + vector search) | 8 | — | Detects duplicate faces with >85% accuracy |
| 2.13 | Create `face_dedup_node.py` | 3 | 2.12 | Flags duplicates, stores embedding if clean |
| 2.14 | Create `kyc_encryption_service.py` (AES-256-GCM) | 5 | — | Encrypts/decrypts all PII fields correctly |
| 2.15 | Create `encrypt_store_node.py` | 2 | 2.14 | All KYC PII encrypted before DB write |
| 2.16 | Create `ckyc_service.py` + `ckyc_upload_node.py` | 5 | 2.4 | Uploads verified KYC to CKYCR, stores CKYC number |
| 2.17 | Rewire `decision_flow.py` graph with all new nodes | 5 | 2.4-2.16 | Graph compiles, checkpointer works, full flow executes |

**Sprint 2 Total: 68 points**

---

## Sprint 3: Decisioning Agent India (2 Weeks)

### Week 1: Regulatory + Policy Layer

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 3.1 | Create `rbi_compliance_gate.py` | 5 | — | Hard rejects NPA, wilful defaulter, underage, no-KYC |
| 3.2 | Create `rbi_compliance_gate_node.py` | 3 | 3.1 | Node wired into graph, routes REJECT/PROCEED |
| 3.3 | Create `bank_policy_engine.py` | 5 | — | Loads JSON config, evaluates per-product rules |
| 3.4 | Create `bank_policy.json` config | 3 | — | Personal, home, education, default products defined |
| 3.5 | Create `bank_policy_node.py` | 3 | 3.3 | Injects policy into state for LLM context |
| 3.6 | Modify `decision_state.py` (CIBIL, RBI fields, KFS) | 3 | — | New state fields compile, no runtime errors |
| 3.7 | Create `cibil-sample-report.json` | 2 | — | Realistic CIBIL TransUnion format |

### Week 2: LLM + KFS + Counter-Offer

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 3.8 | Modify `credit_score_node.py` for CIBIL 300-900 range | 3 | 3.7 | Score bands correct for Indian ranges |
| 3.9 | Modify `income_node.py` for Indian salary (basic, HRA, PF) | 3 | — | Parses Indian salary structure correctly |
| 3.10 | Modify all other risk nodes for INR / Indian norms | 5 | 3.7 | All 7 nodes produce valid output from CIBIL data |
| 3.11 | Create RBI-aware LLM prompt | 5 | 3.1, 3.3 | Prompt includes all 7 RBI mandatory constraints |
| 3.12 | Modify `decision_llm_node.py` with RBI context injection | 5 | 3.11 | LLM receives policy + RBI constraints in every call |
| 3.13 | Create `kfs_generator.py` | 5 | — | KFS contains APR, fees, GST, cooling-off, ombudsman |
| 3.14 | Create `kfs_node.py` | 2 | 3.13 | KFS generated for APPROVE and COUNTER_OFFER |
| 3.15 | Modify `counter_offer_node.py` for INR + GST | 3 | — | Counter-offer amounts include GST on fees |
| 3.16 | Rewire `decision_flow.py` graph | 3 | 3.2, 3.5, 3.14 | Full graph: PII→RBI→Policy→Parallel→Agg→LLM→KFS→Final |

**Sprint 3 Total: 58 points**

---

## Sprint 4: eSign + Disbursement India (2 Weeks)

### Week 1: eSign + Agreement

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 4.1 | Create `esign_service.py` (Aadhaar eSign provider) | 8 | — | Create/poll/callback lifecycle works |
| 4.2 | Create `docusign_india_service.py` (alternative) | 5 | — | DocuSign with Indian CA integration works |
| 4.3 | Create `loan_agreement_generator.py` (PDF with KFS) | 5 | S3-3.13 | PDF has KFS on page 1, all RBI disclosures |
| 4.4 | Create `generate_agreement_node.py` | 3 | 4.3 | Generates PDF, stores in state |
| 4.5 | Create `esign_gate_node.py` | 5 | 4.1 | Initiates eSign, routes signed/rejected/expired |
| 4.6 | Update `entities.py` with India fields | 3 | — | eSign, NACH, IFSC, UTR fields added |

### Week 2: Fund Transfer + NACH + Loan Kit

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 4.7 | Create `IndiaBankingGateway` (NEFT/RTGS/IMPS) | 5 | — | Auto-selects mode by amount, returns UTR |
| 4.8 | Modify `execute_transfer_node.py` | 3 | 4.7 | Uses India gateway, validates IFSC |
| 4.9 | Create `nach_mandate_service.py` | 5 | — | Creates NACH e-mandate via NPCI API |
| 4.10 | Create `setup_nach_node.py` | 3 | 4.9 | Mandate created, auth URL returned |
| 4.11 | Create `loan_kit_service.py` + `send_loan_kit_node.py` | 3 | — | Sends signed agreement + KFS + schedule via email/SMS |
| 4.12 | Modify `disbursement_calculator.py` (GST, stamp duty) | 3 | — | Processing fee + GST calculated correctly |
| 4.13 | Rewire disbursement graph | 3 | 4.4-4.11 | Full flow: validate→agreement→eSign→schedule→transfer→NACH→receipt→kit |

**Sprint 4 Total: 54 points**

---

## Sprint 5: Orchestrator + Integration (1 Week)

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 5.1 | Update `data_mappers.py` (all 3 mappers for India) | 5 | S1-S4 | Correct field mapping Aadhaar/PAN/CIBIL/eSign |
| 5.2 | Update `pipeline_events.py` (new India events) | 2 | — | All new events defined |
| 5.3 | Update `pipeline_service.py` (eSign step, ₹ formatting) | 5 | S4 | eSign gate between approval and disbursement |
| 5.4 | Add `/confirm_esign` + `/initiate_video_kyc` routes | 3 | 5.3 | Endpoints work, SSE events emit correctly |
| 5.5 | End-to-end integration test (happy path) | 8 | 5.1-5.4 | Full pipeline: Intake→KYC→Decision→eSign→Disburse |
| 5.6 | End-to-end test (rejection paths) | 5 | 5.5 | RBI reject, KYC fail, eSign timeout all handled |

**Sprint 5 Total: 28 points**

---

## Sprint 6: Security + Compliance (1 Week)

| # | Task | Points | Depends On | Acceptance Criteria |
|---|------|:------:|:----------:|---------------------|
| 6.1 | mTLS setup between all agents | 5 | S5 | Inter-agent calls use mutual TLS |
| 6.2 | Encrypt all PII DB columns | 5 | S2-2.14 | No plaintext PII in any DB |
| 6.3 | S3 SSE-KMS for video recordings | 3 | — | All video files encrypted at rest |
| 6.4 | Audit log tamper-proofing (SHA-256 chain) | 3 | — | Log entries include chain hash |
| 6.5 | Data localization verification | 2 | — | All infra in `ap-south-1` / India region |
| 6.6 | Penetration testing on eSign flow | 5 | S4 | No auth bypass, replay attack blocked |
| 6.7 | RBI compliance checklist sign-off | 3 | All | All 12 RBI checkpoints pass |

**Sprint 6 Total: 26 points**

---

## Grand Total

| Sprint | Points | Duration |
|--------|:------:|:--------:|
| Sprint 1 — Intake | 49 | 2 weeks |
| Sprint 2 — KYC | 68 | 2 weeks |
| Sprint 3 — Decisioning | 58 | 2 weeks |
| Sprint 4 — eSign + Disbursement | 54 | 2 weeks |
| Sprint 5 — Orchestrator | 28 | 1 week |
| Sprint 6 — Security | 26 | 1 week |
| **Total** | **283** | **10 weeks** |
