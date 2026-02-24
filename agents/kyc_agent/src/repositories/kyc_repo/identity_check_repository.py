# src/repositories/kyc_repo/kyc_repository.py

from src.models.identity_check import IdentityCheck


class KYCRepository:
    ...

    async def create_identity_check(
        self,
        kyc_id,
        applicant_id: str,
        final_status: str,
        risk_payload: dict,
    ):
        record = IdentityCheck(
            kyc_id=kyc_id,
            applicant_id=applicant_id,
            final_status=final_status,
            risk_payload=risk_payload,
        )
        self.db.add(record)
        await self.db.flush()
        return record
