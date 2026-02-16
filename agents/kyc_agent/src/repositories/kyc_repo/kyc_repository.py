# src/repositories/kyc_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.kyc_cases import KYCAttempt
from src.models.enums import KYCStatus
import uuid


async def get_attempt_by_idempotency(
    db: AsyncSession,
    idempotency_key: str,
) -> KYCAttempt | None:
    
    
    result = await db.execute(
        select(KYCAttempt).where(
            KYCAttempt.idempotency_key == idempotency_key
        )
    )
    return result.scalar_one_or_none()


async def create_kyc_attempt(
    db: AsyncSession,
    application_id: str
) -> KYCAttempt:

    attempt = KYCAttempt(
        application_id=application_id,
        status=KYCStatus.PENDING,
    )

    db.add(attempt)
    await db.flush()      # gets ID without commit
    await db.refresh(attempt)
    return attempt
