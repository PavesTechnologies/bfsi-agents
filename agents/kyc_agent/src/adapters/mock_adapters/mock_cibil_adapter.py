# src/adapters/mock_adapters/mock_cibil_adapter.py
"""
Mock CIBIL TransUnion Credit Report Adapter (Indian Bureau)

Scenario selection is driven by the 4-digit numeric segment of the PAN (positions 5–8):

  Range       Scenario
  ─────────────────────────────────────────────────────────────
  0001–2499   Prime borrower            (CIBIL score 780)
  2500–4999   Good borrower             (CIBIL score 730)
  5000–5999   High revolving utilization(CIBIL score 660)
  6000–6999   Subprime / late payments  (CIBIL score 580)
  7000–7499   Written-off account       (CIBIL score 510)
  7500–7999   New to Credit (NH / -1)   (CIBIL score -1)
  8000–8499   Suit filed / DRT case     (CIBIL score 490)
  8500–8999   Wilful defaulter          (CIBIL score 300)
  9000–9999   Moderate / default profile(CIBIL score 700)

Output field names mirror the Experian-compatible schema so the
existing 7 parallel decisioning nodes work without modification:
  riskModel, tradeline, inquiry, publicRecord, summaries, consumerIdentity, addressInformation
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST
# ─────────────────────────────────────────────────────────────────────────────


class CIBILRequestPayload(BaseModel):
    pan: str
    full_name: str
    dob: str = ""  # YYYY-MM-DD, optional for mock

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        v = v.upper().strip()
        if len(v) != 10:
            raise ValueError("PAN must be exactly 10 characters")
        if not v[:5].isalpha():
            raise ValueError("PAN first 5 characters must be alphabetic")
        if not v[5:9].isdigit():
            raise ValueError("PAN characters 6–9 must be numeric")
        if not v[9].isalpha():
            raise ValueError("PAN check digit must be alphabetic")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE MODELS  (CIBIL-native names, Experian-compatible keys on output)
# ─────────────────────────────────────────────────────────────────────────────


class CIBILScoreModel(BaseModel):
    """Mirrors Experian riskModel entry so credit_score_node reads score unchanged."""
    modelIndicator: str = "CIBIL TransUnion Score 2.0"
    score: str                          # "300"–"900" or "-1" for NH (New to Credit)
    scoreFactors: list[dict[str, str]]


class CIBILConsumerIdentity(BaseModel):
    """Mirrors Experian consumerIdentity; pi_deletion_node strips name/dob fields."""
    name: list[dict[str, str]]          # [{"firstName": ..., "surname": ...}]
    dob: dict[str, str]                 # {"day": ..., "month": ..., "year": ...}
    phone: list[dict[str, str]]
    pan: str                            # pre-masked, e.g. "ABCDE****F"


class CIBILAddressInfo(BaseModel):
    streetNumber: str
    streetName: str
    city: str
    state: str                          # 2-char state code, e.g. "MH"
    pinCode: str                        # Indian PIN (6 digits)
    source: str


class CIBILTradeline(BaseModel):
    """
    Mirrors Experian tradeline.  Key fields consumed by decisioning nodes:
      revolvingOrInstallment  – "R" (credit card/OD) | "I" (EMI loan)
      openOrClosed            – "O" (active)         | "C" (closed/settled/written-off)
      monthlyPaymentAmount    – EMI or minimum payment (INR, string)
      delinquencies30Days     – count of 30-DPD events (string)
      dpdHistory              – list of 3-char DPD codes, one per month (last 36)
    """
    accountType: str
    subscriberName: str
    accountNumber: str                  # masked, e.g. "****7821"
    ownershipType: str                  # "Individual" | "Joint"
    dateOpened: str                     # YYYY-MM-DD
    creditLimitOrSanctionedAmount: str  # INR
    balanceAmount: str                  # current outstanding INR
    amountOverdue: str                  # overdue INR
    monthlyPaymentAmount: str           # EMI / minimum payment INR
    status: str                         # "Active" | "Closed" | "Settled" | "Written Off"
    openOrClosed: str                   # "O" | "C"
    revolvingOrInstallment: str         # "R" | "I"
    delinquencies30Days: str            # count as string
    dpdHistory: list[str]               # 36 monthly DPD codes ["000", "000", "030", ...]
    closedDate: Optional[str] = None


class CIBILPublicRecord(BaseModel):
    """
    Mirrors Experian publicRecord.
    pi_deletion_node removes courtName and referenceNumber before LLM sees this.
    """
    type: str               # "SUIT_FILED" | "DRT_CASE" | "WILFUL_DEFAULT" | "WRITTEN_OFF_AS_FRAUD"
    status: str             # "Pending" | "Decree" | "Resolved"
    amount: str             # INR
    filingDate: str         # YYYY-MM-DD
    courtName: Optional[str] = None        # stripped by pi_deletion
    referenceNumber: Optional[str] = None  # stripped by pi_deletion
    wilfulDefaulter: bool = False


class CIBILInquiry(BaseModel):
    """Mirrors Experian inquiry list consumed by inquiry_node."""
    date: str
    subscriberName: str
    purpose: str            # "Personal Loan" | "Home Loan" | "Credit Card" | etc.
    enquiryAmount: str      # INR


class CIBILResponse(BaseModel):
    """
    Full CIBIL credit report response.

    Top-level keys deliberately match Experian field names (riskModel, tradeline,
    inquiry, publicRecord, summaries, consumerIdentity, addressInformation) so the
    existing decisioning nodes work with zero changes.
    """
    reportId: str
    reportDate: str

    # ── Experian-compatible keys (read directly by 7 decisioning nodes) ──
    consumerIdentity: CIBILConsumerIdentity
    addressInformation: list[CIBILAddressInfo]
    riskModel: list[CIBILScoreModel]
    tradeline: list[CIBILTradeline]
    publicRecord: list[CIBILPublicRecord]
    inquiry: list[CIBILInquiry]
    summaries: list[dict[str, Any]]     # tradeSummary with revolvingCreditUtilization

    # ── CIBIL-specific metadata ──
    wilfulDefaulterFlag: bool = False
    suitFiledFlag: bool = False
    writtenOffFlag: bool = False
    ntcFlag: bool = False               # New To Credit


# ─────────────────────────────────────────────────────────────────────────────
# ADAPTER
# ─────────────────────────────────────────────────────────────────────────────


class MockCIBILAdapter:
    """
    Mock CIBIL TransUnion credit report adapter.

    Usage:
        adapter = MockCIBILAdapter()
        report: CIBILResponse = await adapter.get_credit_report(
            {"pan": "ABCDE1234F", "full_name": "Ravi Kumar"}
        )
    """

    async def get_credit_report(
        self, raw_payload: dict[str, Any]
    ) -> CIBILResponse:
        request = CIBILRequestPayload(**raw_payload)
        numeric_segment = int(request.pan[5:9])

        if 1 <= numeric_segment <= 2499:
            return self._prime_profile(request)
        elif 2500 <= numeric_segment <= 4999:
            return self._good_profile(request)
        elif 5000 <= numeric_segment <= 5999:
            return self._high_utilization_profile(request)
        elif 6000 <= numeric_segment <= 6999:
            return self._subprime_profile(request)
        elif 7000 <= numeric_segment <= 7499:
            return self._written_off_profile(request)
        elif 7500 <= numeric_segment <= 7999:
            return self._ntc_profile(request)
        elif 8000 <= numeric_segment <= 8499:
            return self._suit_filed_profile(request)
        elif 8500 <= numeric_segment <= 8999:
            return self._wilful_defaulter_profile(request)
        else:
            return self._moderate_profile(request)

    # ─────────────────────────── SHARED BUILDERS ────────────────────────────

    def _identity(self, req: CIBILRequestPayload) -> dict[str, Any]:
        parts = req.full_name.upper().split() if req.full_name.strip() else ["APPLICANT"]
        first = parts[0]
        surname = parts[-1] if len(parts) > 1 else ""
        return {
            "name": [{"firstName": first, "surname": surname}],
            "dob": {"day": "15", "month": "06", "year": "1988"},
            "phone": [{"number": "9876543210", "type": "Mobile"}],
            "pan": req.pan[:5] + "****" + req.pan[-1],
        }

    def _build(
        self,
        req: CIBILRequestPayload,
        score: int,
        tradelines: list[dict],
        inquiries: list[dict],
        public_records: list[dict],
        score_factors: list[dict],
        wilful_defaulter: bool = False,
        suit_filed: bool = False,
        written_off: bool = False,
        ntc: bool = False,
    ) -> CIBILResponse:
        today = datetime.now().strftime("%Y-%m-%d")
        identity = self._identity(req)

        revolving = [t for t in tradelines if t.get("revolvingOrInstallment") == "R"]
        total_limit = sum(int(t.get("creditLimitOrSanctionedAmount", 0)) for t in revolving)
        total_rev_bal = sum(int(t.get("balanceAmount", 0)) for t in revolving)
        utilization_pct = (
            round(total_rev_bal / total_limit * 100, 1) if total_limit > 0 else 0.0
        )

        return CIBILResponse(
            reportId=f"CIBIL-{uuid.uuid4().hex[:12].upper()}",
            reportDate=today,
            consumerIdentity=CIBILConsumerIdentity(**identity),
            addressInformation=[
                CIBILAddressInfo(
                    streetNumber="12",
                    streetName="MG Road",
                    city="Bengaluru",
                    state="KA",
                    pinCode="560001",
                    source="Residential",
                )
            ],
            riskModel=[
                CIBILScoreModel(score=str(score), scoreFactors=score_factors)
            ],
            tradeline=[CIBILTradeline(**t) for t in tradelines],
            publicRecord=[CIBILPublicRecord(**p) for p in public_records],
            inquiry=[CIBILInquiry(**i) for i in inquiries],
            summaries=[
                {
                    "summaryType": "tradeSummary",
                    "attributes": [
                        {"id": "revolvingCreditUtilization", "value": str(utilization_pct)},
                        {"id": "totalAccounts", "value": str(len(tradelines))},
                        {
                            "id": "activeAccounts",
                            "value": str(sum(1 for t in tradelines if t.get("openOrClosed") == "O")),
                        },
                    ],
                }
            ],
            wilfulDefaulterFlag=wilful_defaulter,
            suitFiledFlag=suit_filed,
            writtenOffFlag=written_off,
            ntcFlag=ntc,
        )

    # ─────────────────────── SCENARIO 1: PRIME (0001–2499) ──────────────────

    def _prime_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        tradelines = [
            {
                "accountType": "Home Loan",
                "subscriberName": "SBI",
                "accountNumber": "****7821",
                "ownershipType": "Individual",
                "dateOpened": "2019-03-10",
                "creditLimitOrSanctionedAmount": "4500000",
                "balanceAmount": "3200000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "32000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
            {
                "accountType": "Credit Card",
                "subscriberName": "HDFC Bank",
                "accountNumber": "****4490",
                "ownershipType": "Individual",
                "dateOpened": "2017-06-15",
                "creditLimitOrSanctionedAmount": "150000",
                "balanceAmount": "28000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "3000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "R",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
            {
                "accountType": "Personal Loan",
                "subscriberName": "Bajaj Finance",
                "accountNumber": "****1102",
                "ownershipType": "Individual",
                "dateOpened": "2016-01-20",
                "creditLimitOrSanctionedAmount": "300000",
                "balanceAmount": "0",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "0",
                "status": "Closed",
                "openOrClosed": "C",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
                "closedDate": "2019-01-20",
            },
        ]
        inquiries = [
            {"date": "2025-11-10", "subscriberName": "ICICI Bank", "purpose": "Home Loan", "enquiryAmount": "5000000"},
            {"date": "2025-08-22", "subscriberName": "Axis Bank", "purpose": "Personal Loan", "enquiryAmount": "500000"},
        ]
        return self._build(
            req, score=780, tradelines=tradelines, inquiries=inquiries,
            public_records=[],
            score_factors=[{"code": "05", "description": "Long and clean credit history with no defaults"}],
        )

    # ─────────────────────── SCENARIO 2: GOOD (2500–4999) ───────────────────

    def _good_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        tradelines = [
            {
                "accountType": "Home Loan",
                "subscriberName": "HDFC Bank",
                "accountNumber": "****9923",
                "ownershipType": "Individual",
                "dateOpened": "2020-07-01",
                "creditLimitOrSanctionedAmount": "3500000",
                "balanceAmount": "2800000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "28000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
            {
                "accountType": "Credit Card",
                "subscriberName": "SBI Card",
                "accountNumber": "****3312",
                "ownershipType": "Individual",
                "dateOpened": "2018-09-20",
                "creditLimitOrSanctionedAmount": "100000",
                "balanceAmount": "38000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "2500",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "R",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
            {
                "accountType": "Auto Loan",
                "subscriberName": "Kotak Mahindra Bank",
                "accountNumber": "****7714",
                "ownershipType": "Individual",
                "dateOpened": "2022-02-14",
                "creditLimitOrSanctionedAmount": "600000",
                "balanceAmount": "420000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "12000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
        ]
        inquiries = [
            {"date": "2025-12-05", "subscriberName": "YES Bank", "purpose": "Personal Loan", "enquiryAmount": "400000"},
            {"date": "2025-09-18", "subscriberName": "HDFC Bank", "purpose": "Credit Card", "enquiryAmount": "0"},
            {"date": "2025-06-30", "subscriberName": "Bajaj Finance", "purpose": "Consumer Loan", "enquiryAmount": "150000"},
        ]
        return self._build(
            req, score=730, tradelines=tradelines, inquiries=inquiries,
            public_records=[],
            score_factors=[{"code": "01", "description": "Moderate revolving balance relative to credit limit"}],
        )

    # ─────────────────── SCENARIO 3: HIGH UTILIZATION (5000–5999) ───────────

    def _high_utilization_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        tradelines = [
            {
                "accountType": "Credit Card",
                "subscriberName": "HDFC Bank",
                "accountNumber": "****2201",
                "ownershipType": "Individual",
                "dateOpened": "2019-03-10",
                "creditLimitOrSanctionedAmount": "80000",
                "balanceAmount": "72000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "4000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "R",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
            {
                "accountType": "Credit Card",
                "subscriberName": "ICICI Bank",
                "accountNumber": "****8874",
                "ownershipType": "Individual",
                "dateOpened": "2020-07-22",
                "creditLimitOrSanctionedAmount": "60000",
                "balanceAmount": "55000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "3000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "R",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
            {
                "accountType": "Credit Card",
                "subscriberName": "Axis Bank",
                "accountNumber": "****5566",
                "ownershipType": "Individual",
                "dateOpened": "2021-01-05",
                "creditLimitOrSanctionedAmount": "50000",
                "balanceAmount": "47000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "2500",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "R",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
            {
                "accountType": "Personal Loan",
                "subscriberName": "Bajaj Finance",
                "accountNumber": "****9931",
                "ownershipType": "Individual",
                "dateOpened": "2023-04-10",
                "creditLimitOrSanctionedAmount": "250000",
                "balanceAmount": "180000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "8500",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
        ]
        inquiries = [
            {"date": "2026-01-10", "subscriberName": "IndusInd Bank", "purpose": "Personal Loan", "enquiryAmount": "300000"},
            {"date": "2025-11-25", "subscriberName": "Tata Capital", "purpose": "Personal Loan", "enquiryAmount": "200000"},
            {"date": "2025-09-12", "subscriberName": "Bajaj Finance", "purpose": "Consumer Loan", "enquiryAmount": "100000"},
            {"date": "2025-07-08", "subscriberName": "SBI", "purpose": "Personal Loan", "enquiryAmount": "500000"},
            {"date": "2025-04-15", "subscriberName": "ICICI Bank", "purpose": "Credit Card", "enquiryAmount": "0"},
        ]
        return self._build(
            req, score=660, tradelines=tradelines, inquiries=inquiries,
            public_records=[],
            score_factors=[
                {"code": "01", "description": "Proportion of revolving balances to limits too high (>85%)"},
                {"code": "04", "description": "Too many enquiries in the last 12 months"},
            ],
        )

    # ─────────────────────── SCENARIO 4: SUBPRIME (6000–6999) ──────────────

    def _subprime_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        dpd_with_late = (
            ["000"] * 12 + ["030"] + ["000"] * 6 + ["060"] + ["000"] * 16
        )
        tradelines = [
            {
                "accountType": "Personal Loan",
                "subscriberName": "YES Bank",
                "accountNumber": "****4432",
                "ownershipType": "Individual",
                "dateOpened": "2021-05-15",
                "creditLimitOrSanctionedAmount": "400000",
                "balanceAmount": "310000",
                "amountOverdue": "12000",
                "monthlyPaymentAmount": "14000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "2",
                "dpdHistory": dpd_with_late,
            },
            {
                "accountType": "Credit Card",
                "subscriberName": "SBI Card",
                "accountNumber": "****7723",
                "ownershipType": "Individual",
                "dateOpened": "2020-02-10",
                "creditLimitOrSanctionedAmount": "75000",
                "balanceAmount": "68000",
                "amountOverdue": "5000",
                "monthlyPaymentAmount": "3500",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "R",
                "delinquencies30Days": "1",
                "dpdHistory": ["000"] * 12 + ["030"] + ["000"] * 23,
            },
            {
                "accountType": "Two Wheeler Loan",
                "subscriberName": "Bajaj Finance",
                "accountNumber": "****1188",
                "ownershipType": "Individual",
                "dateOpened": "2019-10-01",
                "creditLimitOrSanctionedAmount": "85000",
                "balanceAmount": "0",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "0",
                "status": "Closed",
                "openOrClosed": "C",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "1",
                "dpdHistory": ["000"] * 20 + ["030"] + ["000"] * 15,
                "closedDate": "2022-10-01",
            },
        ]
        inquiries = [
            {"date": "2026-02-14", "subscriberName": "IndusInd Bank", "purpose": "Personal Loan", "enquiryAmount": "300000"},
            {"date": "2025-12-10", "subscriberName": "IIFL Finance", "purpose": "Gold Loan", "enquiryAmount": "150000"},
            {"date": "2025-10-05", "subscriberName": "Muthoot Finance", "purpose": "Gold Loan", "enquiryAmount": "100000"},
            {"date": "2025-08-20", "subscriberName": "Kotak Bank", "purpose": "Personal Loan", "enquiryAmount": "250000"},
            {"date": "2025-06-15", "subscriberName": "Tata Capital", "purpose": "Personal Loan", "enquiryAmount": "200000"},
            {"date": "2025-04-01", "subscriberName": "Bajaj Finance", "purpose": "Consumer Loan", "enquiryAmount": "80000"},
        ]
        return self._build(
            req, score=580, tradelines=tradelines, inquiries=inquiries,
            public_records=[],
            score_factors=[
                {"code": "03", "description": "Level of delinquency on accounts"},
                {"code": "01", "description": "High revolving utilization on credit card"},
                {"code": "04", "description": "Excessive enquiries in last 12 months"},
            ],
        )

    # ────────────────────── SCENARIO 5: WRITTEN-OFF (7000–7499) ────────────

    def _written_off_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        tradelines = [
            {
                "accountType": "Personal Loan",
                "subscriberName": "IndusInd Bank",
                "accountNumber": "****3392",
                "ownershipType": "Individual",
                "dateOpened": "2018-06-01",
                "creditLimitOrSanctionedAmount": "500000",
                "balanceAmount": "480000",
                "amountOverdue": "480000",
                "monthlyPaymentAmount": "0",
                "status": "Written Off",
                "openOrClosed": "C",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "12",
                "dpdHistory": (
                    ["000"] * 6
                    + ["030", "060", "090", "090", "090", "120", "120", "120"]
                    + ["SUB", "SUB", "SUB", "DBT", "DBT", "LSS", "LSS", "LSS"]
                    + ["XXX"] * 10
                ),
                "closedDate": "2021-12-01",
            },
            {
                "accountType": "Credit Card",
                "subscriberName": "HDFC Bank",
                "accountNumber": "****6671",
                "ownershipType": "Individual",
                "dateOpened": "2017-03-15",
                "creditLimitOrSanctionedAmount": "120000",
                "balanceAmount": "115000",
                "amountOverdue": "115000",
                "monthlyPaymentAmount": "0",
                "status": "Settled",
                "openOrClosed": "C",
                "revolvingOrInstallment": "R",
                "delinquencies30Days": "8",
                "dpdHistory": (
                    ["000"] * 6
                    + ["030", "060", "090", "120", "SUB", "LSS"]
                    + ["XXX"] * 24
                ),
                "closedDate": "2022-08-01",
            },
            {
                "accountType": "Auto Loan",
                "subscriberName": "Axis Bank",
                "accountNumber": "****2211",
                "ownershipType": "Individual",
                "dateOpened": "2022-01-10",
                "creditLimitOrSanctionedAmount": "700000",
                "balanceAmount": "550000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "16000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
        ]
        inquiries = [
            {"date": "2026-03-01", "subscriberName": "Muthoot Finance", "purpose": "Gold Loan", "enquiryAmount": "200000"},
            {"date": "2026-01-15", "subscriberName": "IIFL Finance", "purpose": "Gold Loan", "enquiryAmount": "150000"},
        ]
        return self._build(
            req, score=510, tradelines=tradelines, inquiries=inquiries,
            public_records=[], written_off=True,
            score_factors=[
                {"code": "02", "description": "Derogatory records: written-off and settled accounts present"},
                {"code": "03", "description": "Severe delinquency history across multiple accounts"},
            ],
        )

    # ──────────────────── SCENARIO 6: NEW TO CREDIT (7500–7999) ────────────

    def _ntc_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        inquiries = [
            {"date": "2026-04-01", "subscriberName": "HDFC Bank", "purpose": "Credit Card", "enquiryAmount": "0"},
        ]
        return self._build(
            req, score=-1, tradelines=[], inquiries=inquiries,
            public_records=[], ntc=True,
            score_factors=[
                {"code": "06", "description": "No credit history on file — New to Credit (NH)"},
            ],
        )

    # ─────────────────────── SCENARIO 7: SUIT FILED (8000–8499) ────────────

    def _suit_filed_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        tradelines = [
            {
                "accountType": "Business Loan",
                "subscriberName": "PNB",
                "accountNumber": "****8821",
                "ownershipType": "Individual",
                "dateOpened": "2017-09-01",
                "creditLimitOrSanctionedAmount": "2000000",
                "balanceAmount": "1850000",
                "amountOverdue": "1850000",
                "monthlyPaymentAmount": "0",
                "status": "Written Off",
                "openOrClosed": "C",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "18",
                "dpdHistory": (
                    ["000"] * 4
                    + ["030", "060", "090", "090", "120", "120"]
                    + ["SUB", "SUB", "DBT", "DBT", "LSS", "LSS"]
                    + ["XXX"] * 20
                ),
                "closedDate": "2022-03-01",
            },
        ]
        public_records = [
            {
                "type": "SUIT_FILED",
                "status": "Pending",
                "amount": "1850000",
                "filingDate": "2022-04-15",
                "courtName": "City Civil Court, Mumbai",
                "referenceNumber": "SUIT/2022/4421",
                "wilfulDefaulter": False,
            },
        ]
        inquiries = [
            {"date": "2025-06-01", "subscriberName": "Kotak Bank", "purpose": "Personal Loan", "enquiryAmount": "300000"},
        ]
        return self._build(
            req, score=490, tradelines=tradelines, inquiries=inquiries,
            public_records=public_records, suit_filed=True,
            score_factors=[
                {"code": "02", "description": "Legal proceedings: civil suit filed against outstanding loan"},
                {"code": "03", "description": "Severe delinquency culminating in charge-off"},
            ],
        )

    # ──────────────────── SCENARIO 8: WILFUL DEFAULTER (8500–8999) ──────────

    def _wilful_defaulter_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        tradelines = [
            {
                "accountType": "Home Loan",
                "subscriberName": "Bank of Baroda",
                "accountNumber": "****3344",
                "ownershipType": "Individual",
                "dateOpened": "2015-04-01",
                "creditLimitOrSanctionedAmount": "8000000",
                "balanceAmount": "7500000",
                "amountOverdue": "7500000",
                "monthlyPaymentAmount": "0",
                "status": "Written Off",
                "openOrClosed": "C",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "24",
                "dpdHistory": (
                    ["090", "090", "090", "120", "120", "120"]
                    + ["SUB"] * 6
                    + ["DBT"] * 6
                    + ["LSS"] * 6
                    + ["XXX"] * 12
                ),
                "closedDate": "2021-06-01",
            },
        ]
        public_records = [
            {
                "type": "WILFUL_DEFAULT",
                "status": "Decree",
                "amount": "7500000",
                "filingDate": "2021-07-01",
                "courtName": "Debt Recovery Tribunal, Mumbai",
                "referenceNumber": "DRT/2021/0099",
                "wilfulDefaulter": True,
            },
        ]
        return self._build(
            req, score=300, tradelines=tradelines, inquiries=[],
            public_records=public_records,
            wilful_defaulter=True, suit_filed=True, written_off=True,
            score_factors=[
                {"code": "02", "description": "Wilful defaulter flag active — RBI mandated hard decline"},
                {"code": "03", "description": "Catastrophic delinquency: 24+ months across all accounts"},
            ],
        )

    # ──────────────────── SCENARIO DEFAULT: MODERATE (9000–9999) ────────────

    def _moderate_profile(self, req: CIBILRequestPayload) -> CIBILResponse:
        tradelines = [
            {
                "accountType": "Personal Loan",
                "subscriberName": "ICICI Bank",
                "accountNumber": "****6612",
                "ownershipType": "Individual",
                "dateOpened": "2021-08-10",
                "creditLimitOrSanctionedAmount": "350000",
                "balanceAmount": "200000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "12000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "I",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
            {
                "accountType": "Credit Card",
                "subscriberName": "Axis Bank",
                "accountNumber": "****9921",
                "ownershipType": "Individual",
                "dateOpened": "2020-04-15",
                "creditLimitOrSanctionedAmount": "80000",
                "balanceAmount": "35000",
                "amountOverdue": "0",
                "monthlyPaymentAmount": "2000",
                "status": "Active",
                "openOrClosed": "O",
                "revolvingOrInstallment": "R",
                "delinquencies30Days": "0",
                "dpdHistory": ["000"] * 36,
            },
        ]
        inquiries = [
            {"date": "2026-02-20", "subscriberName": "HDFC Bank", "purpose": "Home Loan", "enquiryAmount": "3000000"},
            {"date": "2025-10-05", "subscriberName": "Axis Bank", "purpose": "Personal Loan", "enquiryAmount": "400000"},
            {"date": "2025-07-18", "subscriberName": "SBI", "purpose": "Auto Loan", "enquiryAmount": "700000"},
        ]
        return self._build(
            req, score=700, tradelines=tradelines, inquiries=inquiries,
            public_records=[],
            score_factors=[
                {"code": "01", "description": "Moderate revolving utilization (~43%)"},
                {"code": "07", "description": "Multiple active accounts with outstanding balances"},
            ],
        )
