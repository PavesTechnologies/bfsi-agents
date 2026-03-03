import functools
import json
import time

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.persistence import persist_vendor_artifact  # Import your shared logic
from src.models.vendor_response import VendorResponse


def audited_adapter(vendor_name: str, vendor_service: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Context Extraction
            kyc_id = kwargs.get("kyc_id")
            applicant_id = kwargs.get("applicant_id") or kyc_id
            db: AsyncSession = kwargs.get("db")

            if not kyc_id and args and isinstance(args[0], dict):
                kyc_id = args[0].get("applicant_id") or args[0].get("kyc_id")

            start_time = time.time()
            print(
                f"Executing {vendor_name} - {vendor_service} for KYC ID: {kyc_id}"
            )  # Debug log for execution start
            # 2. Execute Adapter
            response = func(*args, **kwargs)

            duration_ms = int((time.time() - start_time) * 1000)
            raw_body = (
                json.dumps(response) if isinstance(response, dict) else str(response)
            )

            # 3. Use Shared Persistence Logic (Handles Hashing & S3)
            # Satisfies: PersistenceHash and PersistenceStore tasks
            persistence_result = persist_vendor_artifact(
                attempt_id=applicant_id, vendor=vendor_name, raw_content=raw_body
            )

            # 4. PersistencePersist: Log metadata to DB
            if db and kyc_id:
                # Extract sanctions version if present in the response
                sanctions_version = (
                    response.get("sanctions_list_version")
                    if isinstance(response, dict)
                    else None
                )
                vendor_log = VendorResponse(
                    kyc_id=kyc_id,
                    vendor_name=vendor_name,
                    vendor_service=f"{vendor_service} (v:{sanctions_version})"
                    if sanctions_version
                    else vendor_service,
                    response_hash=persistence_result["hash"],
                    raw_response_location=persistence_result["s3_uri"],
                    success=True,
                    response_time_ms=duration_ms,
                    http_status_code=200,
                )
                try:
                    async with db.begin_nested():
                        db.add(vendor_log)
                        await db.flush()
                except (
                    sqlalchemy.exc.InvalidRequestError
                ):  # Ensure the log is written to the DB
                    db.add(vendor_log)

            return response

        return wrapper

    return decorator
