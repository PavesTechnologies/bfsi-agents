import re
from enum import StrEnum

# Supports Latin and Devanagari scripts for Indian names
NAME_REGEX = re.compile(r"^[A-Za-zऀ-ॿ\s\-'\.]{1,100}$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^\+91[6-9]\d{9}$")

AADHAAR_REGEX = re.compile(r"^\d{12}$")
AADHAAR_LAST4_REGEX = re.compile(r"^\d{4}$")
# 4th char encodes entity type: P=Individual, C=Company, H=HUF, F=Firm, T=Trust, etc.
PAN_REGEX = re.compile(r"^[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]$")
VOTER_ID_REGEX = re.compile(r"^[A-Z]{3}\d{7}$")

PINCODE_REGEX = re.compile(r"^[1-9]\d{5}$")
IFSC_REGEX = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")

INDIAN_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "GA",
    "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH",
    "ML", "MN", "MP", "MZ", "NL", "OD", "PB", "PY", "RJ", "SK",
    "TN", "TS", "TR", "UK", "UP", "WB",
}

EMPLOYMENT_TYPES = {"salaried", "self_employed", "retired", "unemployed"}


class ApplicantStatusEnum(StrEnum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
