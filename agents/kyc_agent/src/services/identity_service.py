from datetime import date, datetime
import phonenumbers
from src.adapters.mock_adapters.mock_experian_adapter import ExperianResponse
# Assuming the state classes are imported from the domain/models layer
from src.workflows.kyc_engine.kyc_state import ContactVerificationState, RawKYCRequest, SSNValidationState, AddressVerificationState
import dns.resolver
import dns.exception

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

    @staticmethod
    def process_address_verification(request: RawKYCRequest, vendor_data: ExperianResponse) -> AddressVerificationState:
        """
        Coordinates address verification logic (PRD 5.1, 10.1).
        Compares applicant-submitted address against Experian's on-file address.
        Returns a complete AddressVerificationState dictionary.
        """
        req_addr = request["address"]
        exp_addr = vendor_data.addressInformation[0]

        # 1. Normalize for comparison
        req_line1 = req_addr.get("line1", "").strip().upper()
        exp_line1 = f"{exp_addr.streetNumber} {exp_addr.streetName}".strip().upper()
        if exp_addr.streetSuffix:
            exp_line1 += f" {exp_addr.streetSuffix.upper()}"

        req_city = req_addr.get("city", "").strip().upper()
        req_state = req_addr.get("state", "").strip().upper()
        req_zip = req_addr.get("zip", "").strip()

        # 2. Field-level matching
        city_match = req_city == exp_addr.city.upper()
        state_match = req_state == exp_addr.state.upper()
        zip_match = req_zip[:5] == exp_addr.zipCode[:5]
        street_match = req_line1 == exp_line1

        # 3. Compute risk score (0.0 = perfect, 1.0 = worst)
        match_count = sum([street_match, city_match, state_match, zip_match])
        risk_score = round(1.0 - (match_count / 4.0), 2)

        address_match = match_count >= 3  # At least 3 of 4 fields must match

        # 4. Flags
        flags = {}
        if not street_match:
            flags["STREET_MISMATCH"] = f"Request: {req_line1} vs Vendor: {exp_line1}"
        if not city_match:
            flags["CITY_MISMATCH"] = f"Request: {req_city} vs Vendor: {exp_addr.city}"
        if not state_match:
            flags["STATE_MISMATCH"] = f"Request: {req_state} vs Vendor: {exp_addr.state}"
        if not zip_match:
            flags["ZIP_MISMATCH"] = f"Request: {req_zip} vs Vendor: {exp_addr.zipCode}"

        # 5. Standardized address from vendor
        standardized_address = {
            "line1": exp_line1,
            "city": exp_addr.city.upper(),
            "state": exp_addr.state.upper(),
            "zip": exp_addr.zipCode,
        }

        # 6. Address type from vendor source field
        address_type = exp_addr.source  # e.g. "Residential", "Commercial"

        return {
            "address_match": address_match,
            "risk_score": risk_score,
            "geo_risk_flag": False,
            "high_risk_country_flag": False,
            "address_type": address_type,
            "usps_validated": False,
            "deliverable": address_match,
            "standardized_address": standardized_address,
            "flags": flags,
        }
    
    @staticmethod
    def process_contact_verification(request: RawKYCRequest) -> ContactVerificationState:
        """
        Implements PRD 5.1 & 6.1: Phone/Email ownership and validity checks.
        Handles E.164 formatting, VOIP detection, and MX record verification.
        """
        phone = request.get("phone", "")
        email = request.get("email", "")
        flags = {}
        
        # --- 1. Phone Validation (Libphonenumber) ---
        phone_valid = False
        is_high_risk_phone = False
        formatted_phone = phone

        try:
            # Assumes default region US for parsing (PRD 5.1)
            parsed_phone = phonenumbers.parse(phone, "US")
            phone_valid = phonenumbers.is_valid_number(parsed_phone)
            formatted_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
            
            # Burner/VOIP Detection logic (PRD 6.1)
            p_type = phonenumbers.number_type(parsed_phone)
            if p_type in [phonenumbers.PhoneNumberType.VOIP, phonenumbers.PhoneNumberType.PERSONAL_NUMBER]:
                is_high_risk_phone = True
                flags["PHONE_RISK"] = "VOIP or Burner number detected"

        except Exception:
            flags["PHONE_ERROR"] = "Invalid phone format"

        # --- 2. Email Validation (MX & Disposable) ---
        email_valid = False
        is_disposable_email = False
        
        # Example disposable domain list (In production, move to a Repository/Adapter)
        disposable_domains = {"mailinator.com", "guerrillamail.com", "tempmail.com"}
        domain = email.split('@')[-1].lower() if '@' in email else ""

        if domain:
            # Check Disposable Blacklist (PRD 6.1)
            if domain in disposable_domains:
                is_disposable_email = True
                flags["EMAIL_DISPOSABLE"] = "Disposable email service detected"
            
            # MX Record Verification
            try:
                dns.resolver.resolve(domain, 'MX')
                email_valid = True
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, Exception):
                email_valid = False
                flags["EMAIL_DOMAIN_ERROR"] = "No valid MX records found"

        return {
            "phone_valid": phone_valid,
            "email_valid": email_valid,
            "is_high_risk_phone": is_high_risk_phone,
            "is_disposable_email": is_disposable_email,
            "formatted_phone": formatted_phone,
            "flags": flags
        }