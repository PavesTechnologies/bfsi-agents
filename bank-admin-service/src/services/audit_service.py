import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.bank_user import BankAdminAuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        before: Optional[dict] = None,
        after: Optional[dict] = None,
        ip_address: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        entry = BankAdminAuditLog(
            user_id=uuid.UUID(user_id) if user_id else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            before_snapshot=before,
            after_snapshot=after,
            ip_address=ip_address,
            extra=extra,
        )
        self.db.add(entry)
        await self.db.flush()
