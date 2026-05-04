from typing import Optional

from src.models.interfaces.identity_validation import CrossValidationResult, FieldMismatch
from src.repositories.intake_repo.applicant_repo import ApplicantDAO
from src.repositories.intake_repo.address_repo import AddressDAO


def _name_tokens_match(doc_name: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> bool:
    """
    Return True if all tokens in the applicant's stored name appear in the
    document name — regardless of order (handles first/last reversal) and
    ignoring middle names present only in the document.
    Returns True (no mismatch) when doc_name is None so we never raise a
    false positive when name extraction failed.
    """
    if not doc_name:
        return True

    doc_tokens = {t.upper() for t in doc_name.split() if t}
    app_tokens: set[str] = set()
    for part in filter(None, [first_name, last_name]):
        app_tokens.update(t.upper() for t in part.split() if t)

    if not app_tokens:
        return True

    return app_tokens.issubset(doc_tokens)


class CrossValidationService:
    def __init__(self, applicant_dao : ApplicantDAO = None, address_dao : AddressDAO = None):
        self.applicant_dao = applicant_dao or ApplicantDAO()
        self.address_dao = address_dao or AddressDAO()
        
    async def validate_passport(
        self,
        application_id: str,
        normalized_data: dict,
    ) -> CrossValidationResult:
        
        # normalized_data : 
        # {'document_type': 'PASSPORT', 'issuing_country': 'USA', 'nationality': 'USA', 'last_name': 'MEHTA', 'first_name': 'ROHAN ANIL', 'passport_number': 'P98765432', 'date_of_birth': '1993-09-14', 'expiry_date': '2029-01-11', 'gender': 'MALE'}


        applicant = await self.applicant_dao.get_primary_by_application_id(application_id)
        if not applicant:
            raise Exception("Applicant not found")

        mismatches = []
        print(applicant.__dict__)

        # last name
        if "last_name" in normalized_data and applicant.last_name and applicant.last_name.upper() != normalized_data["last_name"].upper():
            mismatches.append(FieldMismatch(
                field="last_name",
                expected=applicant.last_name,
                actual=normalized_data["last_name"]
            ))
        else:
            print(f"Last name matches: {applicant.last_name} / {normalized_data.get('last_name')}")

        # first name)
        if "first_name" in normalized_data and applicant.first_name and applicant.first_name.upper() not in normalized_data["first_name"].upper():
            mismatches.append(FieldMismatch(
                field="first_name",
                expected=applicant.first_name,
                actual=normalized_data["first_name"]
            ))

        # Date of birth
        if "date_of_birth" in normalized_data and str(applicant.date_of_birth) != normalized_data["date_of_birth"]:
            mismatches.append(FieldMismatch(
                field="date_of_birth",
                expected=str(applicant.date_of_birth),
                actual=normalized_data["date_of_birth"]
            ))

        # Nationality
        if "nationality" in normalized_data and hasattr(applicant, "nationality") and applicant.nationality and applicant.nationality.upper() != normalized_data["nationality"].upper():
            mismatches.append(FieldMismatch(
                field="nationality",
                expected=getattr(applicant, "nationality", None),
                actual=normalized_data["nationality"]
            ))

        # Passport number
        if "passport_number" in normalized_data and hasattr(applicant, "passport_number") and applicant.passport_number and applicant.passport_number != normalized_data["passport_number"]:
            mismatches.append(FieldMismatch(
                field="passport_number",
                expected=getattr(applicant, "passport_number", None),
                actual=normalized_data["passport_number"]
            ))

        # Gender (optional, if available)
        if "gender" in normalized_data and applicant.gender and str(applicant.gender.value).upper() != normalized_data["gender"].upper():
            mismatches.append(FieldMismatch(
                field="gender", 
                expected=getattr(applicant, "gender", None).value if hasattr(applicant, "gender") else None,
                actual=normalized_data["gender"]
            ))


        return CrossValidationResult(
            valid=len(mismatches) == 0,
            mismatches=mismatches
        )

    async def validate_aadhaar(
        self,
        application_id: str,
        normalized_data: dict,
    ) -> CrossValidationResult:
        """
        Cross-validate OCR-extracted Aadhaar fields against the application.
        Fields not extracted by OCR (None) are silently skipped — no false positives.
        Name comparison is order-insensitive to handle first/last reversal on the card.
        """
        applicant = await self.applicant_dao.get_primary_by_application_id(application_id)
        if not applicant:
            raise Exception("Applicant not found")

        mismatches = []

        # Name — token-set match handles reversal and middle names
        if not _name_tokens_match(
            normalized_data.get("full_name"),
            applicant.first_name,
            applicant.last_name,
        ):
            mismatches.append(FieldMismatch(
                field="name",
                expected=f"{applicant.first_name} {applicant.last_name}",
                actual=normalized_data.get("full_name"),
            ))

        # DOB
        doc_dob = normalized_data.get("date_of_birth")
        if doc_dob and applicant.date_of_birth and str(applicant.date_of_birth) != doc_dob:
            mismatches.append(FieldMismatch(
                field="date_of_birth",
                expected=str(applicant.date_of_birth),
                actual=doc_dob,
            ))

        # Aadhaar last 4 digits (full number is encrypted; only last4 stored in plain)
        doc_last4 = normalized_data.get("aadhaar_last4")
        if doc_last4 and applicant.aadhaar_last4 and applicant.aadhaar_last4 != doc_last4:
            mismatches.append(FieldMismatch(
                field="aadhaar_last4",
                expected=applicant.aadhaar_last4,
                actual=doc_last4,
            ))

        # Gender
        doc_gender = normalized_data.get("gender")
        if doc_gender and applicant.gender and applicant.gender.value.upper() != doc_gender.upper():
            mismatches.append(FieldMismatch(
                field="gender",
                expected=applicant.gender.value,
                actual=doc_gender,
            ))

        return CrossValidationResult(valid=len(mismatches) == 0, mismatches=mismatches)

    async def validate_pan(
        self,
        application_id: str,
        normalized_data: dict,
    ) -> CrossValidationResult:
        """
        Cross-validate OCR-extracted PAN fields against the application.
        """
        applicant = await self.applicant_dao.get_primary_by_application_id(application_id)
        if not applicant:
            raise Exception("Applicant not found")

        mismatches = []

        # Name — order-insensitive token match
        if not _name_tokens_match(
            normalized_data.get("full_name"),
            applicant.first_name,
            applicant.last_name,
        ):
            mismatches.append(FieldMismatch(
                field="name",
                expected=f"{applicant.first_name} {applicant.last_name}",
                actual=normalized_data.get("full_name"),
            ))

        # DOB
        doc_dob = normalized_data.get("date_of_birth")
        if doc_dob and applicant.date_of_birth and str(applicant.date_of_birth) != doc_dob:
            mismatches.append(FieldMismatch(
                field="date_of_birth",
                expected=str(applicant.date_of_birth),
                actual=doc_dob,
            ))

        # PAN number — exact match against stored pan_number
        doc_pan = normalized_data.get("pan_number")
        if doc_pan and applicant.pan_number and applicant.pan_number.upper() != doc_pan.upper():
            mismatches.append(FieldMismatch(
                field="pan_number",
                expected=applicant.pan_number,
                actual=doc_pan,
            ))

        return CrossValidationResult(valid=len(mismatches) == 0, mismatches=mismatches)

    async def validate_voter_id(
        self,
        application_id: str,
        normalized_data: dict,
    ) -> CrossValidationResult:
        """
        Cross-validate OCR-extracted Voter ID (EPIC) fields against the application.
        """
        applicant = await self.applicant_dao.get_primary_by_application_id(application_id)
        if not applicant:
            raise Exception("Applicant not found")

        mismatches = []

        # Name — order-insensitive token match
        if not _name_tokens_match(
            normalized_data.get("full_name"),
            applicant.first_name,
            applicant.last_name,
        ):
            mismatches.append(FieldMismatch(
                field="name",
                expected=f"{applicant.first_name} {applicant.last_name}",
                actual=normalized_data.get("full_name"),
            ))

        return CrossValidationResult(valid=len(mismatches) == 0, mismatches=mismatches)

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

    async def validate_ssn(self, application_id: str, ssn_data: dict) -> CrossValidationResult:
        # Similar structure to the above methods, comparing SSN data with applicant info
        
        applicant = await self.applicant_dao.get_primary_by_application_id(application_id)
        if not applicant:
            raise Exception("Applicant not found")

        mismatches = []

        if str(applicant.ssn_last4) != ssn_data["ssn_number"][-4:]:
            mismatches.append(
                FieldMismatch(
                    field="ssn number last 4 digits",
                    expected=str(applicant.ssn_last4),
                    actual=ssn_data["ssn_number"][-4:],
                )
            )

        return CrossValidationResult(
            valid=len(mismatches) == 0,
            mismatches=mismatches
        )