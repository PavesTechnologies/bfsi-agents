# src/repositories/kyc_attempt_repository.py

from sqlalchemy import select, func
from datetime import datetime

from src.models.kyc_attempt import KYCAttempt
from src.models.risk_decision import RiskDecision
from src.models.enums import KYCStatus, FinalDecision


class KYCAttemptRepository:

    def __init__(self, session):
        self.session = session

    def get_latest_attempt(self, application_id, idempotency_key):
        stmt = (
            select(KYCAttempt)
            .where(
                KYCAttempt.application_id == application_id,
                KYCAttempt.idempotency_key == idempotency_key,
            )
            .order_by(KYCAttempt.attempt_version.desc())
            .limit(1)
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_max_attempt_version(self, application_id):
        stmt = select(func.max(KYCAttempt.attempt_version)).where(
            KYCAttempt.application_id == application_id
        )
        result = self.session.execute(stmt)
        return result.scalar() or 0

    def create_attempt(
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
            status=KYCStatus.PENDING,
        )
        self.session.add(attempt)
        self.session.commit()
        self.session.refresh(attempt)
        return attempt

    def update_attempt_status(self, attempt_id, final_decision: FinalDecision, confidence_score: float):

        stmt = select(KYCAttempt).where(KYCAttempt.id == attempt_id)
        result = self.session.execute(stmt)
        attempt = result.scalar_one()

        if final_decision == FinalDecision.PASS:
            attempt.status = KYCStatus.PASSED
        elif final_decision == FinalDecision.FAIL:
            attempt.status = KYCStatus.FAILED
        else:
            attempt.status = KYCStatus.REVIEW

        attempt.confidence_score = confidence_score
        attempt.completed_at = datetime.utcnow()

        self.session.commit()

    def create_risk_decision(self, attempt_id, decision_data):
        decision = RiskDecision(
            kyc_attempt_id=attempt_id,
            final_status=decision_data["final_status"],
            aggregated_score=decision_data.get("confidence_score"),
            hard_fail_triggered=False,
            decision_reason=decision_data.get("reason"),
            decision_rules_snapshot=decision_data,
            model_versions={"engine": "v1"},
        )
        self.session.add(decision)
        self.session.commit()
        return decision
