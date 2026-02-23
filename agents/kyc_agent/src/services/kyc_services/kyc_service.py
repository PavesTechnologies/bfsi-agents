from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.models.enums import IdempotencyStatus
from src.repositories.kyc_repo.kyc_repository import KYCRepository
from src.utils.hash_utils import generate_payload_hash


class KYCService:
    """
    Business logic layer for KYC operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KYCRepository(db)

    # ---------------------------------------------------------
    # Trigger KYC
    # ---------------------------------------------------------
    async def trigger_kyc(
        self,
        payload: dict,
    ) -> dict:
        """
        Handles KYC trigger logic with idempotency enforcement.
        """

        payload_hash = generate_payload_hash(payload)
        idempotency_key = payload["idempotency_key"]

        # -----------------------------------------------------
        # 1️⃣ Check idempotency
        # -----------------------------------------------------
        existing_request = await self.repo.get_request_by_idempotency(
            idempotency_key=idempotency_key,
        )

        if existing_request:

            # 🔒 Validate payload integrity
            if existing_request.payload_hash != payload_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key reused with different payload",
                )

            if existing_request.response_status == IdempotencyStatus.PENDING:
                raise HTTPException(
                    status_code=202,
                    detail={
                        "attempt_id": str(existing_request.kyc_id),
                        "kyc_status": existing_request.response_status.value,
                        "message": "KYC is still processing. Please check back later."
                    }
                )
            
            # If response already stored → return it
            if existing_request.response_payload and existing_request.response_status == IdempotencyStatus.SUCCESS:
                
                if existing_request.response_payload:
                    return existing_request.response_payload

            # Rare edge case
            return {
                "attempt_id": str(existing_request.kyc_id),
                "kyc_status": existing_request.response_status.value,
            }

        # -----------------------------------------------------
        # 2️⃣ Create new KYC case
        # -----------------------------------------------------
        kyc_case = await self.repo.create_kyc_case(
            applicant_id=payload["applicant_id"],
            payload_hash=payload_hash,
            raw_request_payload=payload,  # ✅ NEW
        )

        response_payload = {
            "attempt_id": str(kyc_case.id),
            "kyc_status": kyc_case.status.value,
        }

        # -----------------------------------------------------
        # 3️⃣ Store idempotency record
        # -----------------------------------------------------
        await self.repo.create_kyc_request(
            kyc_id=kyc_case.id,
            idempotency_key=idempotency_key,
            payload_hash=payload_hash,
            response_payload=response_payload,
        )

        return response_payload
