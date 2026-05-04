"""
Mock CKYC (Central KYC Registry) Upload Adapter.

Simulates uploading verified KYC data to the CERSAI CKYC registry.
Generates a deterministic 14-digit CKYC identifier from the applicant_id.

Scenario trigger (first 4 digits of Aadhaar):
  3333 → upload status PENDING (registry acknowledgement delayed)
  Default → SUCCESS with 14-digit CKYC ID
"""

import hashlib
from datetime import datetime, timezone
from typing import Any

from src.workflows.kyc_engine.india_kyc_state import CKYCState


class MockCKYCAdapter:
    """
    Mock CKYC registry (CERSAI) upload adapter.

    Scenario triggers (Aadhaar first 4 digits):
      3333 → PENDING (acknowledgement delayed, retry in 24h)
      Default → SUCCESS with deterministic 14-digit CKYC ID
    """

    def upload(
        self, applicant_id: str, aadhaar_prefix: str, kyc_payload: dict[str, Any]
    ) -> CKYCState:
        # Deterministic 14-digit ID: SHA-256 of applicant_id, truncated to 14 decimal digits
        hash_int = int(hashlib.sha256(applicant_id.encode()).hexdigest(), 16)
        ckyc_id = str(hash_int % (10 ** 14)).zfill(14)

        if aadhaar_prefix == "3333":
            return CKYCState(
                ckyc_id=None,
                upload_status="PENDING",
                uploaded_at=None,
                flags={"CKYC_PENDING": "CKYC registry acknowledgement delayed; retry upload in 24 hours"},
            )

        return CKYCState(
            ckyc_id=ckyc_id,
            upload_status="SUCCESS",
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            flags={},
        )
