import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.disbursement_record import DisbursementRecord
from src.core.database import get_db


def _to_json_safe(obj):
    """Recursively convert datetime/date objects to ISO strings for JSONB storage."""
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_json_safe(v) for v in obj]
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return obj


class DisbursementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_record(self, receipt_data: dict):
        ts_raw = receipt_data.get("transfer_timestamp")
        if isinstance(ts_raw, str) and ts_raw:
            ts_raw = datetime.datetime.fromisoformat(ts_raw)

        record = DisbursementRecord(
            application_id=receipt_data.get("application_id"),
            transaction_id=receipt_data.get("transaction_id"),
            status=receipt_data.get("disbursement_status"),
            disbursement_amount=receipt_data.get("disbursement_amount"),
            transfer_timestamp=ts_raw,
            monthly_emi=receipt_data.get("monthly_emi"),
            total_interest=receipt_data.get("total_interest"),
            total_repayment=receipt_data.get("total_repayment"),
            repayment_schedule={"schedule": receipt_data.get("schedule_preview")},
            receipt_payload=_to_json_safe(receipt_data),
        )
        self.session.add(record)
        await self.session.commit()
        return record
