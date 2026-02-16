# src/services/kyc_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.kyc_repo.kyc_repository import (
    get_attempt_by_idempotency,
    create_kyc_attempt,
)
from src.models.kyc_attempt import KYCAttempt

async def trigger_kyc_service(
    db: AsyncSession,
    application_id: str,
    idempotency_key: str,
) -> KYCAttempt:

    # 1️⃣ Check idempotency
    existing_attempt = await get_attempt_by_idempotency(
        db,
        idempotency_key
    )

    if existing_attempt:
        return existing_attempt

    # 2️⃣ Create new attempt
    attempt = await create_kyc_attempt(
        db=db,
        application_id=application_id,
        idempotency_key=idempotency_key,
    )

    return attempt