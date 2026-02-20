from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator

# --- REQUEST MODELS ---

class ExperianRequestPayload(BaseModel):
    firstName: str
    lastName: str
    street1: str
    street2: Optional[str] = None
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip: str
    ssn: str

    @field_validator('ssn')
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
    name: List[Name]
    dob: DOB
    phone: List[Phone]

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
    indicator: List[str]

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
    scoreFactors: List[ScoreFactor]

class Attribute(BaseModel):
    id: str
    value: str

class Summary(BaseModel):
    summaryType: str
    attributes: List[Attribute]

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
    addressInformation: List[AddressInformation]
    ssn: List[SSNRecord]
    fraudShield: List[FraudShield]
    riskModel: List[RiskModel]
    summaries: List[Summary]
    tradeline: List[Tradeline]
    publicRecord: List[PublicRecord]
    inquiry: List[Dict[str, str]] = []

# --- ADAPTER ---

class MockExperianAdapter:
    """
    Mock for Experian Credit Profile API using Pydantic for validation.
    """

    def get_credit_report(self, raw_payload: Dict[str, Any]) -> ExperianResponse:
        # Validate Input
        request = ExperianRequestPayload(**raw_payload)
        
        area_number = int(request.ssn[:3])
        
        # Scenario Logic
        if 545 <= area_number <= 573:
            return self._build_response(request, score="750", fraud_code="00")
        elif 574 <= area_number <= 576:
            return self._build_response(request, score="580", fraud_code="01", has_bk=True)
        else:
            return self._build_response(request, score="680", fraud_code="00")

    def _build_response(self, req: ExperianRequestPayload, score: str, fraud_code: str, has_bk: bool = False) -> ExperianResponse:    #has_bk = has bankruptcy record
        street_parts = req.street1.split(" ", 1)
        st_num = street_parts[0] if street_parts else "123"
        st_name = street_parts[1] if len(street_parts) > 1 else "MAIN"

        data = {
            "consumerIdentity": {
                "name": [{"firstName": req.firstName.upper(), "surname": req.lastName.upper()}],
                "dob": {"day": "15", "month": "04", "year": "1980"},
                "phone": [{"number": "5551234567", "type": "Residential"}]
            },
            "addressInformation": [{
                "streetNumber": st_num,
                "streetName": st_name.upper(),
                "city": req.city.upper(),
                "state": req.state.upper(),
                "zipCode": req.zip,
                "source": "Residential"
            }],
            "ssn": [{"number": req.ssn, "ssnIndicators": "F", "variationIndicator": "N"}],
            "fraudShield": [{
                "addressCount": "1",
                "socialCount": "1",
                "ssnFirstPossibleIssuanceYear": "1980",
                "fraudShieldIndicators": {"indicator": [fraud_code]}
            }],
            "riskModel": [{
                "modelIndicator": "VantageScore 3.0",
                "score": score,
                "scoreFactors": [{"code": "30", "importance": "1"}]
            }],
            "summaries": [{
                "summaryType": "tradeSummary",
                "attributes": [{"id": "revolvingCreditUtilization", "value": "25"}]
            }],
            "tradeline": [{
                "accountType": "Revolving",
                "subscriberName": "BANK OF AMERICA",
                "balanceAmount": "500",
                "status": "Open",
                "delinquencies30Days": "0"
            }],
            "publicRecord": [],
            "inquiry": [{"date": "2023-09-15", "subscriberName": "AUTO LENDER", "type": "Installment"}]
        }

        if has_bk:
            data["publicRecord"].append({"status": "Discharged", "type": "Bankruptcy", "filingDate": "2015-01-01"})

        return ExperianResponse(**data)