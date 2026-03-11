from sqlalchemy.ext.asyncio import AsyncSession
from src.models.disbursement_record import DisbursementRecord
from src.core.database import get_db

class DisbursementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_record(self, receipt_data: dict):
        record = DisbursementRecord(
            application_id=receipt_data.get("application_id"),
            transaction_id=receipt_data.get("transaction_id"),
            status=receipt_data.get("disbursement_status"),
            disbursement_amount=receipt_data.get("disbursement_amount"),
            transfer_timestamp=receipt_data.get("transfer_timestamp"),
            monthly_emi=receipt_data.get("monthly_emi"),
            total_interest=receipt_data.get("total_interest"),
            total_repayment=receipt_data.get("total_repayment"),
            repayment_schedule={"schedule": receipt_data.get("schedule_preview")},
            receipt_payload=receipt_data
        )
        self.session.add(record)
        await self.session.commit()
        return record
