import hashlib
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.db_models import KycCases, VendorResponses
from src.core.logging import logger


class VendorCallbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # 🔐 Step 1 — Signature verification
    def _verify_signature(self, headers, payload) -> bool:
        # TODO: replace with real vendor secret validation
        return True

    # 🔁 Step 2 — Idempotency (hash-level protection)
    async def _is_duplicate_hash(self, response_hash: str) -> bool:
        stmt = select(VendorResponses).where(
            VendorResponses.response_hash == response_hash
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # 🧠 Step 2B — Business idempotency (vendor + txn)
    async def _is_duplicate_vendor_txn(
        self, vendor_name: str, vendor_txn_id: str
    ) -> bool:
        stmt = select(VendorResponses).where(
            VendorResponses.vendor_name == vendor_name,
            VendorResponses.vendor_transaction_id == vendor_txn_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # 🔍 Step 3 — Correlation
    async def _get_kyc_case(self, vendor_txn_id: str):
        stmt = select(KycCases).where(
            KycCases.vendor_transaction_id == vendor_txn_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # 🚀 MAIN
    async def handle_callback(self, payload: dict, headers):
        # ---------- security ----------
        if not self._verify_signature(headers, payload):
            raise Exception("Invalid signature")

        vendor_txn_id = payload.get("transaction_id")
        vendor_name = payload.get("vendor")
        status = payload.get("status")

        if not vendor_txn_id:
            raise Exception("Missing transaction_id")

        if not vendor_name:
            raise Exception("Missing vendor name")

        # ---------- idempotency (hash) ----------
        response_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()

        if await self._is_duplicate_hash(response_hash):
            logger.info("Duplicate callback ignored (hash match)")
            return {"message": "duplicate ignored"}

        # ---------- idempotency (vendor txn) ----------
        if await self._is_duplicate_vendor_txn(vendor_name, vendor_txn_id):
            logger.info(
                f"Duplicate callback ignored for vendor={vendor_name}, txn={vendor_txn_id}"
            )
            return {"message": "duplicate ignored"}

        # ---------- correlation ----------
        kyc_case = await self._get_kyc_case(vendor_txn_id)

        if not kyc_case:
            logger.warning(
                f"Unknown vendor transaction id: {vendor_txn_id}"
            )
            await self._store_vendor_response(
                None,
                payload,
                response_hash,
                vendor_name,
                vendor_txn_id,
                success=False,
            )
            await self.db.commit()
            return {"message": "unknown transaction id"}

        # ---------- store response ----------
        await self._store_vendor_response(
            kyc_case.id,
            payload,
            response_hash,
            vendor_name,
            vendor_txn_id,
            success=True,
        )

        # ---------- status handling ----------
        if status == "Completed":
            await self._trigger_risk(kyc_case.id)

        await self.db.commit()
        return {"message": "callback processed"}

    # 💾 Store vendor response
    async def _store_vendor_response(
        self,
        kyc_id,
        payload,
        response_hash,
        vendor_name,
        vendor_txn_id,
        success: bool,
    ):
        record = VendorResponses(
            kyc_id=kyc_id,
            vendor_name=vendor_name,
            vendor_transaction_id=vendor_txn_id,  # ⭐ IMPORTANT
            vendor_service=payload.get("service"),
            response_hash=response_hash,
            raw_response_location=json.dumps(payload),
            success=success,
            created_at=datetime.utcnow(),
        )
        self.db.add(record)

    # 🎯 Trigger risk
    async def _trigger_risk(self, kyc_id: int):
        logger.info(f"Risk should be triggered for kyc_id={kyc_id}")