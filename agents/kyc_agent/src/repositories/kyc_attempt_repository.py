# src/repositories/kyc_attempt_repository.py

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.models.kyc_models import KYCAttempt, RiskDecision


class KYCAttemptRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_attempt(self, application_id, idempotency_key):
        stmt = (
            select(KYCAttempt)
            .where(
                KYCAttempt.application_id == application_id,
                KYCAttempt.idempotency_key == idempotency_key,
            )
            .order_by(KYCAttempt.attempt_version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_max_attempt_version(self, application_id):
        stmt = select(func.max(KYCAttempt.attempt_version)).where(
            KYCAttempt.application_id == application_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def create_attempt(
        self,
        application_id,
        idempotency_key,
        payload_hash,
        attempt_version,
    ):
        attempt = KYCAttempt(
            application_id=application_id,
            idempotency_key=idempotency_key,
            payload_hash=payload_hash,
            attempt_version=attempt_version,
            status="PENDING",
            created_at=datetime.utcnow(),
        )
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def update_attempt_status(self, attempt_id, status):
        stmt = select(KYCAttempt).where(KYCAttempt.id == attempt_id)
        result = await self.session.execute(stmt)
        attempt = result.scalar_one()
        attempt.status = status
        attempt.completed_at = datetime.utcnow()
        await self.session.commit()

    async def create_risk_decision(self, attempt_id, decision_data):
        decision = RiskDecision(
            kyc_attempt_id=attempt_id,
            final_status=decision_data["final_status"],
            aggregated_score=decision_data.get("confidence_score"),
            decision_rules_snapshot=decision_data,
            created_at=datetime.utcnow(),
        )
        self.session.add(decision)
        await self.session.commit()
        return decision
