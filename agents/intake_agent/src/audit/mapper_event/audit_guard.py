from sqlalchemy import event
from src.models.models import AuditLogs


@event.listens_for(AuditLogs, "before_update")
def block_audit_update(mapper, connection, target):
    raise RuntimeError("UPDATE is not allowed on audit_logs (immutable table)")


@event.listens_for(AuditLogs, "before_delete")
def block_audit_delete(mapper, connection, target):
    raise RuntimeError("DELETE is not allowed on audit_logs (immutable table)")
