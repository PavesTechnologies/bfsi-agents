# src/models/enums.py

from enum import StrEnum


class KYCStatus(StrEnum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    REVIEW = "REVIEW"
    FAILED = "FAILED"


class FinalDecision(StrEnum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


class ArtifactType(StrEnum):
    ID_IMAGE = "ID_IMAGE"
    SELFIE = "SELFIE"
    VENDOR_JSON = "VENDOR_JSON"
    LOG_SNAPSHOT = "LOG_SNAPSHOT"


class ActorType(StrEnum):
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"


class HumanReviewDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REUPLOAD_REQUESTED = "REUPLOAD_REQUESTED"


class IdempotencyStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
