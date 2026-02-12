from src.models.interfaces.identity_validation import CrossValidationResult, FieldMismatch
from src.repositories.intake_repo.applicant_repo import ApplicantDAO
from src.repositories.intake_repo.address_repo import AddressDAO

class CrossValidationService:
    def __init__(self, applicant_dao : ApplicantDAO = None, address_dao : AddressDAO = None):
        self.applicant_dao = applicant_dao or ApplicantDAO()
        self.address_dao = address_dao or AddressDAO()
        
    async def validate_passport(
        self,
        application_id: str,
        mrz_data: dict,
    ) -> CrossValidationResult:
        applicant = await self.applicant_dao.get_primary_by_application_id(application_id)
        if not applicant:
            raise Exception("Applicant not found")

        mismatches = []

        # Surname (last name)
        if "surname" in mrz_data and applicant.last_name and applicant.last_name.upper() != mrz_data["surname"].upper():
            mismatches.append(FieldMismatch(
                field="surname",
                expected=applicant.last_name,
                actual=mrz_data["surname"]
            ))

        # Given name (first name)
        if "given_name" in mrz_data and applicant.first_name and applicant.first_name.upper() != mrz_data["given_name"].upper():
            mismatches.append(FieldMismatch(
                field="given_name",
                expected=applicant.first_name,
                actual=mrz_data["given_name"]
            ))

        # Date of birth
        if "date_of_birth" in mrz_data and str(applicant.date_of_birth) != mrz_data["date_of_birth"]:
            mismatches.append(FieldMismatch(
                field="date_of_birth",
                expected=str(applicant.date_of_birth),
                actual=mrz_data["date_of_birth"]
            ))

        # Nationality
        if "nationality" in mrz_data and hasattr(applicant, "nationality") and applicant.nationality and applicant.nationality.upper() != mrz_data["nationality"].upper():
            mismatches.append(FieldMismatch(
                field="nationality",
                expected=getattr(applicant, "nationality", None),
                actual=mrz_data["nationality"]
            ))

        # Passport number
        if "passport_number" in mrz_data and hasattr(applicant, "passport_number") and applicant.passport_number and applicant.passport_number != mrz_data["passport_number"]:
            mismatches.append(FieldMismatch(
                field="passport_number",
                expected=getattr(applicant, "passport_number", None),
                actual=mrz_data["passport_number"]
            ))

        # Gender (optional, if available)
        def _normalize_gender(value: str) -> str: 
            if not value:
                return ""
            value = str(value).strip().upper()
            if value in ["M", "MALE"]:
                return "M"
            if value in ["F", "FEMALE"]:
              return "F"

            return value

        if "gender" in mrz_data and applicant.gender:
            applicant_gender = (
        applicant.gender.value
        if hasattr(applicant.gender, "value")
        else str(applicant.gender)
    )
            normalized_applicant_gender = _normalize_gender(applicant_gender)
            normalized_mrz_gender = _normalize_gender(mrz_data["gender"])

        if normalized_applicant_gender != normalized_mrz_gender:
            mismatches.append(
            FieldMismatch(
                field="gender",
                expected=applicant_gender,
                actual=mrz_data["gender"],
            )
        )


        return CrossValidationResult(
            valid=len(mismatches) == 0,
            mismatches=mismatches
        )


    async def validate_drivers_license(
        self,
        application_id: str,
        dl_data: dict,   # normalized_data
    ) -> CrossValidationResult:

        applicant = await self.applicant_dao.get_primary_by_application_id(
            application_id
        )

        if not applicant:
            raise Exception("Applicant not found")

        address = await self.address_dao.get_primary_by_applicant_id(
            applicant.applicant_id
        )

        mismatches = []

        # -----------------------
        # Name
        # -----------------------

        if applicant.first_name != dl_data["name"]["first_name"]:
            mismatches.append(
                FieldMismatch(
                    field="first_name",
                    expected=applicant.first_name,
                    actual=dl_data["name"]["first_name"],
                )
            )

        if applicant.middle_name != dl_data["name"]["middle_name"]:
            mismatches.append(
                FieldMismatch(
                    field="middle_name",
                    expected=applicant.middle_name,
                    actual=dl_data["name"]["middle_name"],
                )
            )

        if applicant.last_name != dl_data["name"]["last_name"]:
            mismatches.append(
                FieldMismatch(
                    field="last_name",
                    expected=applicant.last_name,
                    actual=dl_data["name"]["last_name"],
                )
            )

        # -----------------------
        # DOB
        # -----------------------

        if str(applicant.date_of_birth) != dl_data["dob"]:
            mismatches.append(
                FieldMismatch(
                    field="dob",
                    expected=str(applicant.date_of_birth),
                    actual=dl_data["dob"],
                )
            )

        # -----------------------
        # Address
        # -----------------------

        if address:

            if address.address_line1 != dl_data["address"]["line1"]:
                mismatches.append(
                    FieldMismatch(
                        field="address.line1",
                        expected=address.address_line1,
                        actual=dl_data["address"]["line1"],
                    )
                )

            if address.city != dl_data["address"]["city"]:
                mismatches.append(
                    FieldMismatch(
                        field="address.city",
                        expected=address.city,
                        actual=dl_data["address"]["city"],
                    )
                )

            if address.state != dl_data["address"]["state"]:
                mismatches.append(
                    FieldMismatch(
                        field="address.state",
                        expected=address.state,
                        actual=dl_data["address"]["state"],
                    )
                )

            if address.zip_code != dl_data["address"]["zip"]:
                mismatches.append(
                    FieldMismatch(
                        field="address.zip",
                        expected=address.zip_code,
                        actual=dl_data["address"]["zip"],
                    )
                )

        return CrossValidationResult(
            valid=len(mismatches) == 0,
            mismatches=mismatches
        )
