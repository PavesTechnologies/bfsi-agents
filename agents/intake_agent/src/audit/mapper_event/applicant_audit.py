from sqlalchemy import event, inspect
from datetime import date, datetime

from models.models import Applicant
from models.models import AuditLogs


# Fields that should never be stored in audit logs
SENSITIVE_FIELDS = {"ssn_encrypted", "itin_number"}


def serialize(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def mask_last_four(value):
    if value is None:
        return None

    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)

    return "*" * (len(value) - 4) + value[-4:]


def collect_model_data(target):
    """
    Collect all column values from a SQLAlchemy model
    """
    data = {}

    for attr in inspect(target).mapper.column_attrs:
        key = attr.key
        value = getattr(target, key)

        if key in SENSITIVE_FIELDS:
            data[key] = mask_last_four(value)
        else:
            data[key] = serialize(value)

    return data



# ------------------ INSERT ------------------

@event.listens_for(Applicant, "after_insert")
def applicant_after_insert(mapper, connection, target):
    connection.execute(
        AuditLog.__table__.insert().values(
            action="CREATE",
            table_name="applicants",
            record_id=target.id,
            old_data=None,
            new_data=collect_model_data(target)
        )
    )


# ------------------ UPDATE ------------------

@event.listens_for(Applicant, "after_update")
def applicant_after_update(mapper, connection, target):
    state = inspect(target)

    old_data = {}
    new_data = {}

    for attr in state.attrs:
        if not attr.history.has_changes():
            continue

        key = attr.key
        old = attr.history.deleted
        new = attr.history.added

        if key in SENSITIVE_FIELDS:
            old_data[key] = mask_last_four(old[0]) if old else None
            new_data[key] = mask_last_four(new[0]) if new else None
        else:
            old_data[key] = serialize(old[0]) if old else None
            new_data[key] = serialize(new[0]) if new else None

    if not old_data:
        return  # no real changes

    connection.execute(
        AuditLog.__table__.insert().values(
            action="UPDATE",
            table_name="applicants",
            record_id=target.id,
            old_data=old_data,
            new_data=new_data
        )
    )


# ------------------ DELETE ------------------

@event.listens_for(Applicant, "after_delete")
def applicant_after_delete(mapper, connection, target):
    connection.execute(
        AuditLogs.__table__.insert().values(
            action="DELETE",
            table_name="applicants",
            record_id=target.id,
            old_data=collect_model_data(target),
            new_data=None
        )
    )
