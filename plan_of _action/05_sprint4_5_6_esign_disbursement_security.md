# Sprint 4: eSign + Disbursement Agent — India (2 Weeks)

## 4.1 New Pipeline Step: Digital Signature Before Disbursement

### Current USA Flow
```
Decisioning → [APPROVE] → Disbursement (direct)
```

### New India Flow
```
Decisioning → [APPROVE + KFS] → eSign (Aadhaar/DSC) → Disbursement → NACH Setup
```

> **Legal Requirement**: Under the IT Act 2000 and RBI Digital Lending Guidelines, the loan agreement must be digitally signed by the borrower BEFORE any money is disbursed.

---

## 4.2 eSign Service Implementation

### Option A: Aadhaar eSign (Recommended for retail loans)

```python
# services/esign_service.py

class AadhaarESignService:
    """
    Aadhaar-based electronic signature via licensed eSign provider.
    Providers: Leegality, eMudhra, NSDL eGov, Protean (NSDL).
    """

    def __init__(self, provider_url: str, api_key: str, asp_id: str):
        self.provider_url = provider_url
        self.api_key = api_key
        self.asp_id = asp_id  # Application Service Provider ID

    async def create_signing_request(
        self, application_id: str, document_pdf: bytes,
        signer_name: str, signer_aadhaar_last4: str, signer_email: str,
        signer_phone: str,
    ) -> dict:
        """Create an eSign request. Borrower will receive OTP on Aadhaar-linked mobile."""
        import base64
        payload = {
            "asp_id": self.asp_id,
            "document": base64.b64encode(document_pdf).decode(),
            "document_name": f"Loan_Agreement_{application_id}.pdf",
            "signers": [{
                "name": signer_name,
                "identifier": signer_aadhaar_last4,
                "email": signer_email,
                "phone": signer_phone,
                "auth_mode": "OTP",  # OTP on Aadhaar-linked mobile
                "signing_positions": [
                    {"page": "last", "x": 350, "y": 100, "width": 200, "height": 50}
                ],
            }],
            "callback_url": f"https://api.bank.com/esign/callback/{application_id}",
            "expiry_hours": 48,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.provider_url}/esign/create",
                json=payload, headers={"Authorization": f"Bearer {self.api_key}"})
            return resp.json()
            # Returns: {"request_id": "...", "signing_url": "https://...", "status": "PENDING"}

    async def get_signing_status(self, request_id: str) -> dict:
        """Check if the document has been signed."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.provider_url}/esign/status/{request_id}",
                headers={"Authorization": f"Bearer {self.api_key}"})
            return resp.json()
            # Returns: {"status": "SIGNED"|"PENDING"|"EXPIRED"|"REJECTED",
            #           "signed_document_url": "https://...",
            #           "certificate": {"issuer": "...", "serial": "...", "timestamp": "..."}}
```

### Option B: DocuSign with Indian CA Integration

```python
# services/docusign_india_service.py

class DocuSignIndiaService:
    """DocuSign integration with Indian Certifying Authority for legal compliance."""

    def __init__(self, account_id: str, integration_key: str, base_url: str):
        self.account_id = account_id
        self.integration_key = integration_key
        self.base_url = base_url

    async def send_for_signature(self, application_id: str, agreement_pdf: bytes,
                                  borrower_email: str, borrower_name: str) -> dict:
        """Send loan agreement via DocuSign with Aadhaar eSign."""
        from docusign_esign import EnvelopesApi, EnvelopeDefinition, Document, Signer, SignHere, Tabs
        import base64

        document = Document(
            document_base64=base64.b64encode(agreement_pdf).decode(),
            name=f"Loan_Agreement_{application_id}",
            file_extension="pdf", document_id="1"
        )
        signer = Signer(
            email=borrower_email, name=borrower_name,
            recipient_id="1", routing_order="1",
            tabs=Tabs(sign_here_tabs=[
                SignHere(document_id="1", page_number="last",
                        x_position="350", y_position="100")
            ])
        )
        envelope = EnvelopeDefinition(
            email_subject=f"Loan Agreement - {application_id}",
            documents=[document],
            recipients={"signers": [signer]},
            status="sent"
        )
        # ... send via DocuSign API
        return {"envelope_id": "...", "status": "sent", "signing_url": "..."}
```

---

## 4.3 Loan Agreement PDF Generation

```python
# services/loan_agreement_generator.py

class LoanAgreementGenerator:
    """Generate loan agreement PDF with all RBI-mandated disclosures."""

    def generate(self, loan_terms: dict, kfs: dict, borrower: dict, bank: dict) -> bytes:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        import io

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # Page 1: KFS (Key Fact Statement) - MANDATORY first page
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 800, "KEY FACT STATEMENT (KFS)")
        c.setFont("Helvetica", 10)
        c.drawString(50, 780, f"As required under RBI Digital Lending Guidelines 2025")

        y = 750
        kfs_items = [
            ("Loan Amount", f"₹{kfs['loan_amount']:,.2f}"),
            ("Annual Percentage Rate (APR)", f"{kfs['apr']}%"),
            ("Interest Rate (p.a.)", f"{kfs['interest_rate_pa']}% (Reducing Balance)"),
            ("Tenure", f"{kfs['tenure_months']} months"),
            ("EMI Amount", f"₹{kfs['emi_amount']:,.2f}"),
            ("Total Interest Payable", f"₹{kfs['total_interest_payable']:,.2f}"),
            ("Processing Fee", f"₹{kfs['processing_fee']:,.2f}"),
            ("GST on Processing Fee", f"₹{kfs['gst_on_processing_fee']:,.2f}"),
            ("Net Disbursement Amount", f"₹{kfs['net_disbursement']:,.2f}"),
            ("Cooling-Off Period", f"{kfs['cooling_off_period_days']} days"),
            ("Prepayment Penalty", kfs['prepayment_penalty']),
        ]
        for label, value in kfs_items:
            c.drawString(50, y, f"{label}: {value}")
            y -= 20

        # Page 2+: Full loan agreement terms
        c.showPage()
        # ... (full agreement template with schedules)

        # Last page: Grievance redressal + RBI Ombudsman
        c.drawString(50, 100, f"Grievance Officer: {bank.get('grievance_officer')}")
        c.drawString(50, 80, f"RBI Ombudsman: https://cms.rbi.org.in")

        c.save()
        return buffer.getvalue()
```

---

## 4.4 Disbursement Agent Changes

### New Workflow (with eSign gate)

```python
# workflows/decision_flow.py (India Disbursement)
def build_disbursement_graph():
    graph = StateGraph(DisbursementState)

    graph.add_node("validate_decision", validate_decision_node)
    graph.add_node("generate_agreement", generate_agreement_node)   # NEW
    graph.add_node("esign_gate", esign_gate_node)                   # NEW
    graph.add_node("generate_schedule", generate_schedule_node)
    graph.add_node("execute_transfer", execute_transfer_node)       # Modified: NEFT/RTGS/IMPS
    graph.add_node("setup_nach", setup_nach_node)                   # NEW
    graph.add_node("generate_receipt", generate_receipt_node)
    graph.add_node("send_loan_kit", send_loan_kit_node)             # NEW: RBI mandate

    graph.set_entry_point("validate_decision")

    # Route after validation
    graph.add_conditional_edges("validate_decision", route_after_validation,
        {"generate_agreement": "generate_agreement", "generate_receipt": "generate_receipt"})

    graph.add_edge("generate_agreement", "esign_gate")

    # eSign gate: wait for signature or timeout
    graph.add_conditional_edges("esign_gate", route_esign,
        {"signed": "generate_schedule", "rejected": "generate_receipt",
         "expired": "generate_receipt"})

    graph.add_edge("generate_schedule", "execute_transfer")
    graph.add_edge("execute_transfer", "setup_nach")
    graph.add_edge("setup_nach", "generate_receipt")
    graph.add_edge("generate_receipt", "send_loan_kit")
    graph.add_edge("send_loan_kit", END)

    return graph.compile()
```

### Fund Transfer — India Banking Gateway

```python
# services/banking_gateway_india.py

class IndiaBankingGateway:
    """
    Fund transfer via NEFT/RTGS/IMPS.
    RBI Rule: Must disburse DIRECTLY to borrower's bank account.
    No third-party/pass-through accounts allowed.
    """

    async def execute_fund_transfer(self, application_id: str, amount: float,
            beneficiary_account: str, beneficiary_ifsc: str,
            beneficiary_name: str, transfer_mode: str = "AUTO") -> dict:

        # Auto-select mode based on amount
        if transfer_mode == "AUTO":
            if amount >= 200000:
                transfer_mode = "RTGS"  # > ₹2L → RTGS (real-time)
            elif amount >= 50000:
                transfer_mode = "NEFT"  # ₹50K-2L → NEFT (batch)
            else:
                transfer_mode = "IMPS"  # < ₹50K → IMPS (instant)

        payload = {
            "reference_id": application_id,
            "amount": amount,
            "currency": "INR",
            "beneficiary_account": beneficiary_account,
            "beneficiary_ifsc": beneficiary_ifsc,
            "beneficiary_name": beneficiary_name,
            "transfer_mode": transfer_mode,
            "purpose": "LOAN_DISBURSEMENT",
            "narration": f"Loan Disbursement - {application_id}",
        }
        # Call Core Banking System API
        # ... returns transaction_id, UTR number, status
        return {
            "transaction_id": f"TXN-{uuid4().hex[:12].upper()}",
            "utr_number": f"UTR{uuid4().hex[:16].upper()}",
            "status": "SUCCESS",
            "transfer_mode": transfer_mode,
            "amount": amount,
            "currency": "INR",
            "timestamp": datetime.now().isoformat(),
        }
```

### NACH e-Mandate Setup

```python
# services/nach_mandate_service.py

class NACHMandateService:
    """Set up NACH e-mandate for automatic EMI debit."""

    async def create_mandate(self, borrower_account: str, borrower_ifsc: str,
            emi_amount: float, start_date: str, end_date: str,
            max_amount: float, frequency: str = "MONTHLY") -> dict:
        payload = {
            "mandate_type": "NACH_DEBIT",
            "account_number": borrower_account,
            "ifsc_code": borrower_ifsc,
            "amount": emi_amount,
            "max_amount": max_amount,  # Must be >= EMI
            "frequency": frequency,
            "first_collection_date": start_date,
            "final_collection_date": end_date,
            "purpose": "EMI_COLLECTION",
            "authentication": "E_MANDATE",  # Aadhaar OTP / Net Banking
        }
        # Register via NPCI NACH API / Bank's mandate platform
        return {"mandate_id": "...", "status": "PENDING_AUTH", "auth_url": "..."}
```

---

# Sprint 5: Orchestrator Changes (1 Week)

## 5.1 Data Mapper Changes

```diff
# shared/data_mappers.py

# Intake → KYC mapper
- "ssn": applicant.get("ssn", ""),
+ "aadhaar_number": applicant.get("aadhaar_number", ""),
+ "pan_number": applicant.get("pan_number", ""),
+ "aadhaar_otp": applicant.get("aadhaar_otp"),

# Address
- "zip": current_address.get("zip_code", ""),
+ "pin_code": current_address.get("pin_code", ""),
+ "district": current_address.get("district", ""),

# KYC → Decisioning mapper
- "raw_experian_data": raw_experian_data,
+ "raw_credit_bureau_data": cibil_data,
+ "credit_bureau_source": "CIBIL",
+ "kyc_verification_method": kyc_data.get("method"),  # "eKYC"|"V-CIP"
```

## 5.2 New Pipeline Events

```python
# shared/pipeline_events.py — ADD
class PipelineEvent(str, Enum):
    # ... existing events ...
    ESIGN_INITIATED = "ESIGN_INITIATED"
    ESIGN_COMPLETED = "ESIGN_COMPLETED"
    ESIGN_FAILED = "ESIGN_FAILED"
    NACH_MANDATE_CREATED = "NACH_MANDATE_CREATED"
    LOAN_KIT_SENT = "LOAN_KIT_SENT"
    RBI_COMPLIANCE_CHECK = "RBI_COMPLIANCE_CHECK"
    KFS_GENERATED = "KFS_GENERATED"
    VIDEO_KYC_INITIATED = "VIDEO_KYC_INITIATED"
    VIDEO_KYC_COMPLETED = "VIDEO_KYC_COMPLETED"
```

## 5.3 New Orchestrator Route: eSign Confirmation

```python
@router.post("/confirm_esign")
async def confirm_esign(request: ESignConfirmRequest):
    """Resume disbursement after borrower completes eSign."""
    service = PipelineService()
    return await service.resume_after_esign(
        application_id=request.application_id,
        esign_request_id=request.esign_request_id,
    )
```

---

# Sprint 6: Security Hardening (1 Week)

## 6.1 Encryption Audit Checklist

| Checkpoint | Requirement | Implementation |
|-----------|------------|----------------|
| DB columns with PII | AES-256-GCM at rest | `KYCEncryptionService.encrypt_field()` |
| Inter-agent HTTP | mTLS between all 5 agents | Nginx/Envoy sidecar with mutual TLS |
| KYC payloads in transit | Encrypted before transmission | `encrypt_kyc_payload()` on every agent boundary |
| Video recordings | Encrypted S3 bucket (SSE-KMS) | AWS S3 server-side encryption |
| Face embeddings | Encrypted vector store | pgvector with column-level encryption |
| Audit logs | Tamper-proof, immutable | Append-only table + SHA-256 chain hash |
| API keys / secrets | Vault storage | HashiCorp Vault / AWS Secrets Manager |
| Data localization | All data in India region | AWS `ap-south-1` / Azure `centralindia` |

## 6.2 Compliance Testing Matrix

| Test | Validates |
|------|-----------|
| Aadhaar Verhoeff checksum (12-digit) | Intake validation |
| PAN regex + NSDL API mock | Intake validation |
| V-CIP session lifecycle | KYC agent Video KYC |
| Face dedup with duplicate photo | KYC agent dedup |
| RBI gate rejects NPA applicant | Decisioning compliance |
| KFS has APR + cooling-off period | Decisioning output |
| eSign → disbursement gating | Disbursement blocked without signature |
| NACH mandate creation | Repayment setup |
| Encrypted payload between agents | Security hardening |
| Data never leaves `ap-south-1` | Data localization |
