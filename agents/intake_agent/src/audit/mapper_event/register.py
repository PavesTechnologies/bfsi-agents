from sqlalchemy import event
from src.audit.mapper_event.audit_events import (
    after_insert,
    after_update,
    before_delete,
)
from src.models.models import (  # all models you want audited
    Address,
    Applicant,
    Asset,
    Document,
    Employment,
    Income,
    Liability,
    LoanApplication,
    PgsqlDocument,
)

AUDITED_MODELS = [
    LoanApplication,
    Applicant,
    Document,
    Address,
    Asset,
    Employment,
    Income,
    Liability,
    PgsqlDocument,
]


def register_audit_events():
    for model in AUDITED_MODELS:
        event.listen(model, "after_insert", after_insert)
        event.listen(model, "after_update", after_update)
        event.listen(model, "before_delete", before_delete)
