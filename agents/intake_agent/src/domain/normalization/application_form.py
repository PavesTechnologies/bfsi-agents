from copy import deepcopy
import re
import phonenumbers

from src.models.interfaces.Loan_intake_interfaces import LoanIntakeRequest


class RequestNormalizer:
    @staticmethod
    def _clean_str(value: str, upper: bool = False) -> str:
        if not value: return value
        cleaned = value.strip()
        return cleaned.upper() if upper else cleaned

    @staticmethod
    def _clean_numeric(value):
        if value is None:
            return value

        # Convert numeric types to string
        if isinstance(value, (int, float)):
            value = str(value)

        # Ensure it's string before regex
        value = str(value)

        return re.sub(r'\D', '', value)

    

    def format_international_phone(phone_str: str):
        try:
            parsed_num = phonenumbers.parse(phone_str, None) 
            return phonenumbers.format_number(parsed_num, phonenumbers.PhoneNumberFormat.E164)
        except:
            # Fallback to digits only if parsing fails
            return re.sub(r'\D', '', phone_str)

    @classmethod
    def normalize_intake_request(cls, request: LoanIntakeRequest) -> LoanIntakeRequest:
        # Create a deep copy to avoid mutating the original input if needed elsewhere
        req = deepcopy(request)

        # 1. Normalize Loan Level
        req.loan_type = cls._clean_str(req.loan_type)
        req.loan_purpose = cls._clean_str(req.loan_purpose)

        for applicant in req.applicants:
            # 2. Normalize Applicant Level
            applicant.first_name = cls._clean_str(applicant.first_name, upper=True)
            applicant.middle_name = cls._clean_str(applicant.middle_name, upper=True)
            applicant.last_name = cls._clean_str(applicant.last_name, upper=True)
            applicant.suffix = cls._clean_str(applicant.suffix, upper=True)
            applicant.email = cls._clean_str(applicant.email).lower() if applicant.email else None
            applicant.phone_number = cls.format_international_phone(applicant.phone_number)
            applicant.ssn_last4 = cls._clean_str(applicant.ssn_last4)

            # 3. Normalize Addresses
            for addr in applicant.addresses:
                addr.address_line1 = cls._clean_str(addr.address_line1, upper=True)
                addr.address_line2 = cls._clean_str(addr.address_line2, upper=True)
                addr.city = cls._clean_str(addr.city, upper=True)
                addr.state = cls._clean_str(addr.state, upper=True)
                addr.zip_code = cls._clean_numeric(addr.zip_code)

            # 4. Normalize Employment
            if applicant.employment:
                emp = applicant.employment
                emp.employer_name = cls._clean_str(emp.employer_name, upper=True)
                emp.job_title = cls._clean_str(emp.job_title, upper=True)
                emp.employer_phone = cls.format_international_phone(emp.employer_phone)
                emp.employer_address = cls._clean_str(emp.employer_address, upper=True)
                emp.job_title = cls._clean_str(emp.job_title, upper=True)
                emp.gross_monthly_income = cls._clean_numeric(emp.gross_monthly_income)

        return req