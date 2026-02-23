from datetime import date, datetime
from src.adapters.mock_adapters.mock_experian_adapter import ExperianResponse
# Assuming the state classes are imported from the domain/models layer
from src.workflows.kyc_engine.kyc_state import RawKYCRequest, SSNValidationState

class IdentityService:
    """
    Handles core business logic for Identity, DOB, and SSN validation.
    Implements requirements from PRD Sections 5.1, 6.1, and 10.1.
    """

    @staticmethod
    def process_ssn_verification(request: RawKYCRequest, vendor_data: ExperianResponse) -> SSNValidationState:
        """
        Coordinates all SSN-related validation logic (PRD 6.1).
        Returns a complete SSNValidationState dictionary.
        """
        exp_dob = vendor_data.consumerIdentity.dob
        exp_name = vendor_data.consumerIdentity.name[0]
        
        # Formatting for comparison
        vendor_dob_str = f"{exp_dob.year}-{exp_dob.month.zfill(2)}-{exp_dob.day.zfill(2)}"
        vendor_full_name = f"{exp_name.firstName} {exp_name.surname}".lower()
        
        # 1. DOB Logical & Age Sanity (PRD 5.1, 10.1)
        dob_obj = datetime.strptime(request["dob"], "%Y-%m-%d").date()
        today = date.today()
        age = today.year - dob_obj.year - ((today.month, today.day) < (dob_obj.month, dob_obj.day))
        
        flags = {}
        if age < 18: flags["AGE_WARNING"] = "Applicant under 18"
        if age > 120: flags["DOB_ERROR"] = "Age logic violation"
        
        # 2. Name-DOB-SSN Correlation (PRD 6.1)
        dob_match = (vendor_dob_str == request["dob"])
        name_match = (request["full_name"].lower() in vendor_full_name)

        # 3. Construct the state shape defined in kyc_state.py
        return {
            "ssn_valid": age >= 18 and age <= 120,
            "ssn_plausible": age <= 120,
            "identity_theft_flag": False, 
            "deceased_flag": vendor_data.fraudShield[0].dateOfDeath != "",
            "ssn_score": float(vendor_data.riskModel[0].score) / 1000,
            "name_ssn_match": name_match,
            "dob_ssn_match": dob_match,
            "issued_year": int(vendor_data.fraudShield[0].ssnFirstPossibleIssuanceYear),
            "flags": flags
        }
    