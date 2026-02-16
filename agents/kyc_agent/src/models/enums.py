# src/models/enums.py

from enum import Enum


class KYCStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    REVIEW = "REVIEW"
    FAILED = "FAILED"


class FinalDecision(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


class ArtifactType(str, Enum):
    ID_IMAGE = "ID_IMAGE"
    SELFIE = "SELFIE"
    VENDOR_JSON = "VENDOR_JSON"
    LOG_SNAPSHOT = "LOG_SNAPSHOT"


class ActorType(str, Enum):
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"


class HumanReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REUPLOAD_REQUESTED = "REUPLOAD_REQUESTED"


class IdempotencyStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"