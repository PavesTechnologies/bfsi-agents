from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.models.kyc_cases import KYC
from src.models.kyc_request import KYCRequest
from src.models.enums import KYCStatus


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
            select(KYCRequest).where(
                KYCRequest.idempotency_key == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    # ---------------------------------------------------------
    # Create KYC Case
    # ---------------------------------------------------------
    async def create_kyc_case(
        self,
        applicant_id: str,
        payload_hash: str,
    ) -> KYC:

        kyc_case = KYC(
            applicant_id=applicant_id,
            payload_hash=payload_hash,
            status=KYCStatus.PENDING,
        )

        self.db.add(kyc_case)
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
            response_status=response_payload["kyc_status"],
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