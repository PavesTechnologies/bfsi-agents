
import enum

class HumanDecision(enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"

class ApplicantStatus(enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
