# File-Level Change Map: USA → India

## Legend
- 🔴 **DELETE** — Remove entirely (USA-only logic)
- 🟡 **MODIFY** — Change in-place for India
- 🟢 **CREATE** — Brand new file

---

## 1. Intake Agent (`agents/intake_agent/`)

### Models (`src/models/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `models.py` | 🟡 | Remove `ssn_encrypted`, `ssn_last4`, `itin_number`, `suffix`, `citizenship_status`. Add `aadhaar_encrypted`, `aadhaar_last4`, `aadhaar_vid`, `pan_number`, `pan_verified`, `father_name`, `ckyc_number`, `preferred_language`. Change `Address.zip_code` → `pin_code`, add `district`, change `country` default to `'INDIA'`. Change `PgsqlDocument` types from USA docs to India docs. |
| `enums.py` | 🟡 | Add Indian document type enum values |

### Domain — Validation (`src/domain/validation/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `constants.py` | 🟡 | Replace `PHONE_REGEX` (+1→+91), `SSN_REGEX`→`AADHAAR_REGEX`, `ZIP_REGEX`→`PINCODE_REGEX`, `STATE_CODES`→`INDIAN_STATE_CODES` (36 states/UTs), add `PAN_REGEX`, `IFSC_REGEX`, update `NAME_REGEX` for Devanagari |
| `reason_codes.py` | 🟡 | Replace `INVALID_SSN_FORMAT`→`INVALID_AADHAAR_FORMAT`, add `INVALID_PAN_FORMAT`, `INVALID_PINCODE`, `AADHAAR_CHECKSUM_FAILED` |
| `typed_field_validators.py` | 🟡 | Replace `validate_ssn()`→`validate_aadhaar()`, `validate_ssn_last4()`→`validate_aadhaar_last4()`, add `validate_pan()`, `validate_pincode()`, `validate_ifsc()`. Change `validate_phone()` for +91. Change `validate_state()` for Indian states. Change `validate_zip()`→`validate_pincode()` |

### Domain — Document Validation (`src/domain/document_validation/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `ssn_card_doc_validation.py` | 🔴 | USA-only. Delete |
| `usa_driving_licence_validation.py` | 🔴 | AAMVA barcode parsing is USA-only. Delete |
| `aadhaar_validation.py` | 🟢 | Verhoeff checksum, keyword match, QR decode, UIDAI API verify |
| `pan_validation.py` | 🟢 | PAN regex, 4th-char entity type, NSDL API verify |
| `voter_id_validation.py` | 🟢 | EPIC format regex, ECI API verify |
| `india_driving_license_validation.py` | 🟢 | State-format DL number, Vahan/Sarathi API |
| `passport_doc_validation.py` | 🟡 | Keep MRZ parsing, add Indian passport format |
| `bank_statement_validation.py` | 🟢 | PDF parse, IFSC validation, transaction extraction |
| `itr_form16_validation.py` | 🟢 | ITR-V XML parse, PAN cross-reference |
| `salary_slip_validation.py` | 🟢 | OCR extraction, employer match |

### Domain — OCR (`src/domain/ocr/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `aws_textract_ocr.py` | 🟡 | Keep as fallback, but add Hindi lang hint |
| `ocr_dispatcher.py` | 🟡 | Add engine selection logic (Google Vision / Tesseract / Bhashini) |
| `multilingual_ocr.py` | 🟢 | Google Cloud Vision (Hindi+English), Tesseract `hin+eng`, Bhashini API |
| `hindi_postprocessor.py` | 🟢 | Hindi OCR post-processing: common Devanagari error correction, transliteration |

### Domain — Document Classification (`src/domain/document_classification/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `document_type.py` | 🟡 | Replace USA doc types with India doc types |
| `rule_based_classifier.py` | 🟡 | Update keyword rules for Aadhaar, PAN, Voter ID etc. |
| `rules/` | 🟡 | New rule files for each Indian document type |

### Domain — Normalization (`src/domain/normalization/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `drivers_license.py` | 🔴 | USA AAMVA normalizer. Delete |
| `aadhaar_normalizer.py` | 🟢 | Normalize Aadhaar OCR output (name, address, DOB) |
| `pan_normalizer.py` | 🟢 | Normalize PAN OCR output |
| `indian_address_normalizer.py` | 🟢 | Indian address parsing (PIN, district, state) |

### Services (`src/services/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `cross_validation_service.py` | 🟡 | Replace DL cross-validation with Aadhaar/PAN cross-validation against applicant data |
| `zip_processor.py` | 🟢 | ZIP file upload, extraction, per-file classification + validation pipeline |

### API (`src/api/`)
| File | Action | Change Description |
|------|--------|-------------------|
| Routes file | 🟡 | Add `POST /upload-documents-zip/{application_id}` endpoint |

### Core Config (`src/core/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `config.py` | 🟡 | Add `GOOGLE_VISION_CREDENTIALS`, `BHASHINI_API_KEY`, `OCR_ENGINE` settings |

---

## 2. KYC Agent (`agents/kyc_agent/`)

### Models (`src/models/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `kyc_cases.py` | 🟡 | Add `aadhaar_verification`, `pan_verification`, `video_kyc_session`, `face_dedup_result`, `ckyc_record` relationships |
| `ssn_validation.py` | 🔴 | Replace with `aadhaar_verification.py` |
| `aadhaar_verification.py` | 🟢 | DB model for Aadhaar eKYC result storage |
| `pan_verification.py` | 🟢 | DB model for PAN verification result |
| `video_kyc_session.py` | 🟢 | DB model for V-CIP session (audit trail, video URL, geo-tag) |
| `face_dedup_result.py` | 🟢 | DB model for face deduplication check result |
| `ckyc_record.py` | 🟢 | DB model for CKYC registry upload status |

### Workflows (`src/workflows/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `decision_flow.py` | 🟡 | Replace `ssn_node` with `aadhaar_pan_node`. Add `video_kyc_node`, `face_dedup_node`, `ckyc_upload_node`, `encrypt_store_node`. Change graph topology |
| `kyc_engine/kyc_state.py` | 🟡 | Replace `SSNValidationState` with `AadhaarVerificationState`, `PANVerificationState`. Add `VideoKYCState`, `FaceDeduplicationState` |
| `kyc_engine/nodes/ssn.py` | 🔴 | Delete |
| `kyc_engine/nodes/aadhaar_pan.py` | 🟢 | Aadhaar eKYC (UIDAI OTP) + PAN (NSDL) verification node |
| `kyc_engine/nodes/video_kyc.py` | 🟢 | V-CIP session initiation + result polling node |
| `kyc_engine/nodes/face_dedup.py` | 🟢 | Face embedding generation + vector DB dedup check |
| `kyc_engine/nodes/ckyc_upload.py` | 🟢 | Upload verified KYC to Central KYC Registry |
| `kyc_engine/nodes/encrypt_store.py` | 🟢 | Encrypt all PII before final DB storage |
| `kyc_engine/nodes/address.py` | 🟡 | Replace Experian address match with India Post API / Aadhaar address |
| `kyc_engine/nodes/aml.py` | 🟡 | Replace OFAC/SDN with RBI sanctions + UNSC + Indian watchlists |
| `kyc_engine/nodes/contact.py` | 🟡 | Change phone validation to +91, add UPI handle validation |

### Services (`src/services/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `identity_service.py` | 🟡 | Replace SSN/Experian logic with Aadhaar/PAN/CIBIL logic. Change phone region to `"IN"` |
| `face_liveness_service.py` | 🟡 | Uncomment and activate. Integrate with V-CIP provider SDK |
| `video_kyc_service.py` | 🟢 | V-CIP session management (Signzy/HyperVerge integration) |
| `face_dedup_service.py` | 🟢 | Face embedding + vector DB search for deduplication |
| `kyc_encryption_service.py` | 🟢 | AES-256-GCM encryption for all KYC PII fields |
| `ckyc_service.py` | 🟢 | CKYC registry upload/download via CERSAI API |
| `uidai_ekyc_service.py` | 🟢 | UIDAI Aadhaar eKYC (OTP + biometric) API client |
| `pan_verification_service.py` | 🟢 | NSDL/UTI PAN verification API client |

### Adapters (`src/adapters/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `mock_adapters/mock_experian_adapter.py` | 🔴 | Replace with Indian bureau mock |
| `mock_adapters/mock_cibil_adapter.py` | 🟢 | Mock CIBIL TransUnion response |
| `mock_adapters/mock_uidai_adapter.py` | 🟢 | Mock UIDAI eKYC response |

---

## 3. Decisioning Agent (`agents/decisioning_agent/`)

### Workflows (`src/workflows/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `decision_flow.py` | 🟡 | Add `rbi_compliance_gate` and `bank_policy_check` nodes before parallel fan-out. Add `kfs_generation` node after decision. Add conditional routing from RBI gate |
| `decision_state.py` | 🟡 | `raw_experian_data`→`raw_credit_bureau_data`, add `credit_bureau_source`, `rbi_compliance_result`, `bank_policy_result`, `kfs_document` fields |
| `decision_engine/nodes/credit_score_node.py` | 🟡 | Parse CIBIL score (300-900) instead of FICO. Update band thresholds |
| `decision_engine/nodes/rbi_compliance_gate_node.py` | 🟢 | RBI hard rules: age, KYC completion, NPA, wilful defaulter, FLDG cap, cooling-off |
| `decision_engine/nodes/bank_policy_node.py` | 🟢 | Load bank_policy.json, evaluate product-specific thresholds |
| `decision_engine/nodes/kfs_node.py` | 🟢 | Generate Key Fact Statement with APR, fees, cooling-off |
| `decision_engine/nodes/decision_llm_node.py` | 🟡 | Inject RBI context + bank policy into system prompt. Change currency to INR |
| `decision_engine/nodes/counter_offer_node.py` | 🟡 | Add GST on processing fee, INR formatting |
| `decision_engine/nodes/final_response_node.py` | 🟡 | Include KFS in response, INR formatting |
| `decision_engine/nodes/income_node.py` | 🟡 | Adapt for Indian salary structures (basic, HRA, DA, PF) |
| `exp-prequal-fico9.json` | 🔴 | Replace with Indian CIBIL sample |
| `cibil-sample-report.json` | 🟢 | Sample CIBIL TransUnion credit report |

### Domain — Regulatory (`src/domain/regulatory/`) — ALL NEW
| File | Action | Change Description |
|------|--------|-------------------|
| `rbi_compliance_gate.py` | 🟢 | Hard regulatory rules engine |
| `bank_policy_engine.py` | 🟢 | Configurable business rules per product |
| `kfs_generator.py` | 🟢 | Key Fact Statement generator |
| `adverse_action_notice.py` | 🟢 | Indian adverse action notice format |

### Config (`config/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `bank_policy.json` | 🟢 | Product-wise policy config (CIBIL thresholds, DTI limits, rate bands) |

### Services — Prompts (`src/services/prompts/`)
| File | Action | Change Description |
|------|--------|-------------------|
| Underwriting prompt | 🟡 | Replace with India-specific RBI-aware prompt including mandatory constraints |

---

## 4. Disbursement Agent (`agents/disbursment_agent/`)

### Domain (`src/domain/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `entities.py` | 🟡 | Add `kfs_document`, `esign_status`, `esign_request_id`, `signed_agreement_url`, `nach_mandate_id`, `borrower_account`, `borrower_ifsc`, `utr_number` to `DisbursementRequest` and `DisbursementReceipt` |

### Workflows (`src/workflows/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `decision_flow.py` | 🟡 | Add `generate_agreement`, `esign_gate`, `setup_nach`, `send_loan_kit` nodes. Add conditional edge after `esign_gate` |
| `state.py` | 🟡 | Add `agreement_pdf`, `esign_status`, `signed_doc_url`, `nach_mandate`, `loan_kit_sent` fields |
| `nodes/generate_agreement_node.py` | 🟢 | Generate loan agreement PDF with KFS |
| `nodes/esign_gate_node.py` | 🟢 | Initiate Aadhaar eSign, wait/poll for completion |
| `nodes/execute_transfer_node.py` | 🟡 | Use `IndiaBankingGateway` with NEFT/RTGS/IMPS auto-selection. Add IFSC validation |
| `nodes/setup_nach_node.py` | 🟢 | Create NACH e-mandate for EMI auto-debit |
| `nodes/send_loan_kit_node.py` | 🟢 | Email/SMS borrower with signed agreement, KFS, repayment schedule, T&C |

### Services (`src/services/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `banking_gateway.py` | 🟡 | Replace mock with `IndiaBankingGateway` (NEFT/RTGS/IMPS auto-routing, INR, UTR) |
| `esign_service.py` | 🟢 | Aadhaar eSign via licensed provider (Leegality/eMudhra) |
| `docusign_india_service.py` | 🟢 | Alternative: DocuSign with Indian CA integration |
| `loan_agreement_generator.py` | 🟢 | PDF generation with KFS, schedules, RBI disclosures |
| `nach_mandate_service.py` | 🟢 | NACH e-mandate creation via NPCI API |
| `loan_kit_service.py` | 🟢 | Email/SMS delivery of complete digital loan kit |
| `disbursement_calculator.py` | 🟡 | Add GST on processing fee, stamp duty calculation |

---

## 5. Orchestrator (`orchestrator/`)

### Shared (`shared/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `data_mappers.py` | 🟡 | `map_intake_to_kyc`: SSN→Aadhaar/PAN, zip→pin_code. `map_to_underwriting`: Experian→CIBIL. `map_decisioning_to_disbursement`: add KFS, eSign fields. New `map_esign_result` |
| `pipeline_events.py` | 🟡 | Add `ESIGN_*`, `NACH_*`, `VIDEO_KYC_*`, `KFS_*`, `RBI_COMPLIANCE_*` events |

### Services (`src/services/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `pipeline_service.py` | 🟡 | Add eSign step between approval and disbursement. Add `resume_after_esign()`. Change currency formatting $→₹. Add Video KYC wait step |

### API (`src/api/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `routes.py` | 🟡 | Add `POST /confirm_esign`, `POST /initiate_video_kyc`. Modify pipeline flow |

### Models (`src/models/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `pipeline.py` | 🟡 | Add `ESignConfirmRequest`, `VideoKYCInitRequest` models |

### Config (`src/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `config.py` | 🟡 | Add `ESIGN_AGENT_URL` endpoint config |

---

## 6. Infrastructure (`infra/`)
| File | Action | Change Description |
|------|--------|-------------------|
| `docker-compose.yml` | 🟡 | Add eSign agent service, update env vars |
| TLS certificates | 🟢 | mTLS certs for inter-agent encryption |
| Vault config | 🟡 | Add Indian encryption keys, API keys for UIDAI/NSDL/CIBIL |

---

## Summary Counts

| Agent | 🟢 Create | 🟡 Modify | 🔴 Delete | Total Changes |
|-------|:---------:|:---------:|:---------:|:------------:|
| **Intake** | 12 | 11 | 3 | 26 |
| **KYC** | 16 | 7 | 3 | 26 |
| **Decisioning** | 8 | 8 | 1 | 17 |
| **Disbursement** | 8 | 5 | 0 | 13 |
| **Orchestrator** | 0 | 6 | 0 | 6 |
| **Infra** | 1 | 2 | 0 | 3 |
| **Total** | **45** | **39** | **7** | **91** |
