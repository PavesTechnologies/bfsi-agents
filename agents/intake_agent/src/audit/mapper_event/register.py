from sqlalchemy import event
from src.models.models import LoanApplication,Applicant,Document,Address,Asset,Employment,Income,Liability  # all models you want audited

from src.audit.mapper_event.audit_events import after_insert, after_update, before_delete


AUDITED_MODELS =[LoanApplication,Applicant,Document,Address,Asset,Employment,Income,Liability]



def register_audit_events():
    for model in AUDITED_MODELS:
        event.listen(model, "after_insert", after_insert)
        event.listen(model, "after_update", after_update)
        event.listen(model, "before_delete", before_delete)
