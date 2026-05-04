from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.intake_repo.document_upload_repo import LoanIntakeDAO

# Every application must have each of these doc types before triggering.
MANDATORY_DOCS: list[str] = [
    "aadhaar_card",
    "pan_card",
    "photo",
]

# At least one document from each group must be present.
REQUIRED_GROUPS: dict[str, list[str]] = {
    "income_proof": ["salary_slip", "form_16", "itr"],
    "address_proof": [
        "utility_bill",
        "voter_id",
        "driving_license_india",
        "aadhaar_card",
        "address_proof",
        "passport",
    ],
    "bank_proof": ["bank_statement"],
}


@dataclass
class ReadinessResult:
    ready: bool
    missing_mandatory: list[str] = field(default_factory=list)
    missing_groups: dict[str, list[str]] = field(default_factory=dict)

    def to_detail(self) -> dict:
        detail: dict = {"missing_mandatory_documents": self.missing_mandatory}
        if self.missing_groups:
            detail["missing_required_groups"] = {
                group: f"Upload at least one of: {', '.join(accepted)}"
                for group, accepted in self.missing_groups.items()
            }
        return detail


class DocumentReadinessChecker:
    def __init__(self, db: AsyncSession):
        self.dao = LoanIntakeDAO(db)

    async def check(self, application_id: UUID) -> ReadinessResult:
        uploaded = await self.dao.get_uploaded_document_types(application_id)

        missing_mandatory = [d for d in MANDATORY_DOCS if d not in uploaded]

        missing_groups: dict[str, list[str]] = {}
        for group_name, accepted in REQUIRED_GROUPS.items():
            if not any(doc in uploaded for doc in accepted):
                missing_groups[group_name] = accepted

        ready = not missing_mandatory and not missing_groups
        return ReadinessResult(
            ready=ready,
            missing_mandatory=missing_mandatory,
            missing_groups=missing_groups,
        )
