import hashlib
from datetime import datetime

import boto3


def persist_vendor_artifact(attempt_id: str, vendor: str, raw_content: str):
    # 1. Generate SHA-256 Hash
    content_bytes = raw_content.encode("utf-8")
    sha256_hash = hashlib.sha256(content_bytes).hexdigest()

    # 2. Upload to S3
    s3 = boto3.client("s3")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    s3_key = f"audit/{attempt_id}/{vendor}_{timestamp}.json"

    s3.put_object(
        Bucket="dev-kyc-audit-logs",
        Key=s3_key,
        Body=content_bytes,
        ContentType="application/json",
        ServerSideEncryption="AES256",  # Meets PII security
    )

    return {"hash": sha256_hash, "s3_uri": f"s3://dev-kyc-audit-logs/{s3_key}"}
