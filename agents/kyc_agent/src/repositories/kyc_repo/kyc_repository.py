from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enums import IdempotencyStatus, KYCStatus
from src.models.identity_check import IdentityCheck
from src.models.kyc_cases import KYC
from src.models.kyc_request import KYCRequest


class KYCRepository:
    """
    Repository layer for KYC related DB operations.
    """

    def __init__(self, db: AsyncSession):
        
        self.db = db

    # ---------------------------------------------------------
    # Idempotency
    # ---------------------------------------------------------
    async def get_request_by_idempotency(
        self,
        idempotency_key: str,
    ) -> KYCRequest | None:
        result = await self.db.execute(
            select(KYCRequest).where(KYCRequest.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    # ---------------------------------------------------------
    # Create KYC Case
    # ---------------------------------------------------------
    async def create_kyc_case(
        self,
        applicant_id: str,
        payload_hash: str,
        raw_request_payload: dict,
    ) -> KYC:
        kyc_case = KYC(
            applicant_id=applicant_id,
            payload_hash=payload_hash,
            status=KYCStatus.PENDING,
            raw_request_payload=raw_request_payload,  # ✅ NEW
        )

        self.db.add(kyc_case)
        # await self.db.commit()
        await self.db.flush()
        await self.db.refresh(kyc_case)

        return kyc_case

    # ---------------------------------------------------------
    # Create Idempotency Record
    # ---------------------------------------------------------
    async def create_kyc_request(
        self,
        *,
        kyc_id,
        idempotency_key: str,
        payload_hash: str,
        response_payload: dict,
    ) -> KYCRequest:
        request = KYCRequest(
            kyc_id=kyc_id,
            idempotency_key=idempotency_key,
            payload_hash=payload_hash,
            response_payload=response_payload,
            response_status=IdempotencyStatus.SUCCESS,
        )

        self.db.add(request)
        await self.db.flush()
        await self.db.refresh(request)

        return request

    # ---------------------------------------------------------
    # Get Latest Attempt
    # ---------------------------------------------------------
    async def get_latest_attempt(
        self,
        application_id: str,
    ) -> KYC | None:
        """
        Returns the most recent KYC case for an applicant.
        """

        result = await self.db.execute(
            select(KYC)
            .where(KYC.applicant_id == application_id)
            .order_by(desc(KYC.created_at))
            .limit(1)
        )

        return result.scalar_one_or_none()

    # ---------------------------------------------------------
    # Create Identity Check
    # ---------------------------------------------------------
    async def create_identity_check(
        self,
        *,
        kyc_id,
        applicant_id: str,
        final_status: str,
        aggregated_score: float | None = None,
        hard_fail_triggered: bool | None = None,
        ssn_valid: bool | None = None,
        ssn_plausible: bool | None = None,
        name_ssn_match: bool | None = None,
        dob_ssn_match: bool | None = None,
        deceased_flag: bool | None = None,
        ssn_risk_snapshot: dict | None = None,
        decision_rules_snapshot: dict | None = None,
        model_versions: dict | None = None,
        audit_payload: dict | None = None,
    ) -> IdentityCheck:
        record = IdentityCheck(
            kyc_id=kyc_id,
            applicant_id=applicant_id,
            final_status=final_status,
            aggregated_score=aggregated_score,
            hard_fail_triggered=hard_fail_triggered,
            ssn_valid=ssn_valid,
            ssn_plausible=ssn_plausible,
            name_ssn_match=name_ssn_match,
            dob_ssn_match=dob_ssn_match,
            deceased_flag=deceased_flag,
            ssn_risk_snapshot=ssn_risk_snapshot,
            decision_rules_snapshot=decision_rules_snapshot,
            model_versions=model_versions,
            audit_payload=audit_payload,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    # ---------------------------------------------------------
    # Update Idempotency Response
    # ---------------------------------------------------------
    async def update_kyc_request_response(
        self,
        *,
        kyc_id,
        response_payload: dict,
        status: IdempotencyStatus,
    ) -> KYCRequest | None:
        result = await self.db.execute(
            select(KYCRequest).where(KYCRequest.kyc_id == kyc_id)
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        record.response_payload = response_payload
        record.response_status = status

        await self.db.flush()
        await self.db.refresh(record)
        return record
