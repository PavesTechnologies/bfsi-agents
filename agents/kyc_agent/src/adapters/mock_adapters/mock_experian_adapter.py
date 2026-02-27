# src/adapters/mock-adapters/mock_experian_adapter.py

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.adapters.decorators.vendor_audit_decorators import audited_adapter

# --- REQUEST MODELS ---


class ExperianRequestPayload(BaseModel):
    firstName: str
    lastName: str
    street1: str
    street2: str | None = None
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip: str
    ssn: str

    @field_validator("ssn")
    @classmethod
    def clean_ssn(cls, v: str) -> str:
        return v.replace("-", "").strip()


# --- RESPONSE MODELS ---


class Name(BaseModel):
    firstName: str
    surname: str
    generationCode: str = ""


class DOB(BaseModel):
    day: str
    month: str
    year: str


class Phone(BaseModel):
    number: str
    type: str


class ConsumerIdentity(BaseModel):
    name: list[Name]
    dob: DOB
    phone: list[Phone]


class AddressInformation(BaseModel):
    streetNumber: str
    streetName: str
    streetSuffix: str = ""
    city: str
    state: str
    zipCode: str
    source: str


class SSNRecord(BaseModel):
    number: str
    ssnIndicators: str
    variationIndicator: str


class FraudShieldIndicators(BaseModel):
    indicator: list[str]


class FraudShield(BaseModel):
    addressCount: str
    socialCount: str
    dateOfDeath: str = ""
    ssnFirstPossibleIssuanceYear: str
    fraudShieldIndicators: FraudShieldIndicators


class ScoreFactor(BaseModel):
    code: str
    importance: str


class RiskModel(BaseModel):
    modelIndicator: str
    score: str
    scoreFactors: list[ScoreFactor]


class Attribute(BaseModel):
    id: str
    value: str


class Summary(BaseModel):
    summaryType: str
    attributes: list[Attribute]


class Tradeline(BaseModel):
    accountType: str
    subscriberName: str
    balanceAmount: str
    status: str
    delinquencies30Days: str


class PublicRecord(BaseModel):
    status: str
    type: str
    filingDate: str


class ExperianResponse(BaseModel):
    consumerIdentity: ConsumerIdentity
    addressInformation: list[AddressInformation]
    ssn: list[SSNRecord]
    fraudShield: list[FraudShield]
    riskModel: list[RiskModel]
    summaries: list[Summary]
    tradeline: list[Tradeline]
    publicRecord: list[PublicRecord]
    inquiry: list[dict[str, str]] = []


# --- ADAPTER ---


class MockExperianAdapter:
    """
    Mock for Experian Credit Profile API using Pydantic for validation.
    """

    @audited_adapter(vendor_name="EXPERIAN", vendor_service="credit_profile_v3")
    def get_credit_report(
        self, raw_payload: dict[str, Any], **kwargs
    ) -> ExperianResponse:
        request = ExperianRequestPayload(**raw_payload)
        area_number = int(request.ssn[:3])

        # --- VALID PROFILE ---
        if 545 <= area_number <= 573:
            return self._build_response(
                request,
                score="750",
                fraud_code="00",
                dob_override={
                    "year": raw_payload["dob"].split("-")[0],
                    "month": raw_payload["dob"].split("-")[1],
                    "day": raw_payload["dob"].split("-")[2],
                },
            )

        # --- LOW SCORE / BANKRUPTCY ---
        elif 574 <= area_number <= 576:
            return self._build_response(
                request, score="580", fraud_code="01", has_bk=True
            )

        # --- SYNTHETIC SSN (ISSUED AFTER BIRTH) ---
        elif 600 <= area_number <= 619:
            return self._build_response(
                request,
                score="720",
                fraud_code="08",
                issued_year=str(datetime.now().year + 5),
            )

        # --- NAME MISMATCH (IDENTITY THEFT) ---
        elif 620 <= area_number <= 639:
            return self._build_response(
                request,
                score="700",
                fraud_code="04",
                name_override={"firstName": "MICHAEL", "surname": "SMITH"},
            )

        # --- DOB MISMATCH ---
        elif 640 <= area_number <= 659:
            return self._build_response(
                request,
                score="710",
                fraud_code="05",
                dob_override={"day": "01", "month": "01", "year": "1965"},
            )

        # --- DECEASED SSN ---
        elif 660 <= area_number <= 679:
            return self._build_response(
                request, score="500", fraud_code="09", deceased=True
            )

        # --- KNOWN FRAUD HIT ---
        elif 680 <= area_number <= 699:
            return self._build_response(request, score="450", fraud_code="12")

        # --- DEFAULT NORMAL ---
        else:
            return self._build_response(request, score="680", fraud_code="00")

    def _build_response(
        self,
        req: ExperianRequestPayload,
        score: str,
        fraud_code: str,
        has_bk: bool = False,
        dob_override: dict[str, str] | None = None,
        name_override: dict[str, str] | None = None,
        deceased: bool = False,
        issued_year: str = "1980",
    ) -> ExperianResponse:  # has_bk = has bankruptcy record
        street_parts = req.street1.split(" ", 1)
        st_num = street_parts[0] if street_parts else "123"
        st_name = street_parts[1] if len(street_parts) > 1 else "MAIN"

        data: dict[str, Any] = {
            "consumerIdentity": {
                "name": [
                    name_override
                    if name_override
                    else {
                        "firstName": req.firstName.upper(),
                        "surname": req.lastName.upper(),
                    }
                ],
                "dob": dob_override
                if dob_override
                else {"day": "15", "month": "04", "year": "1980"},
                "phone": [{"number": "5551234567", "type": "Residential"}],
            },
            "addressInformation": [
                {
                    "streetNumber": st_num,
                    "streetName": st_name.upper(),
                    "city": req.city.upper(),
                    "state": req.state.upper(),
                    "zipCode": req.zip,
                    "source": "Residential",
                }
            ],
            "ssn": [
                {"number": req.ssn, "ssnIndicators": "F", "variationIndicator": "N"}
            ],
            "fraudShield": [
                {
                    "addressCount": "1",
                    "socialCount": "1",
                    "ssnFirstPossibleIssuanceYear": issued_year,
                    "dateOfDeath": "2018-01-01" if deceased else "",
                    "fraudShieldIndicators": {"indicator": [fraud_code]},
                }
            ],
            "riskModel": [
                {
                    "modelIndicator": "VantageScore 3.0",
                    "score": score,
                    "scoreFactors": [{"code": "30", "importance": "1"}],
                }
            ],
            "summaries": [
                {
                    "summaryType": "tradeSummary",
                    "attributes": [{"id": "revolvingCreditUtilization", "value": "25"}],
                }
            ],
            "tradeline": [
                {
                    "accountType": "Revolving",
                    "subscriberName": "BANK OF AMERICA",
                    "balanceAmount": "500",
                    "status": "Open",
                    "delinquencies30Days": "0",
                }
            ],
            "publicRecord": [],
            "inquiry": [
                {
                    "date": "2023-09-15",
                    "subscriberName": "AUTO LENDER",
                    "type": "Installment",
                }
            ],
        }

        if has_bk:
            data["publicRecord"].append(
                {
                    "status": "Discharged",
                    "type": "Bankruptcy",
                    "filingDate": "2015-01-01",
                }
            )

        if fraud_code == "01":
            data["consumerIdentity"]["dob"] = {
                "day": "01",
                "month": "01",
                "year": "1970",
            }

        return ExperianResponse(**data)
