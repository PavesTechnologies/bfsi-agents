import re
from enum import Enum

NAME_REGEX = re.compile(r"^[A-Za-z\s\-']{1,50}$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^\+1\d{10}$")

SSN_REGEX = re.compile(r"^\d{3}-\d{2}-\d{4}$")
SSN_LAST4_REGEX = re.compile(r"^\d{4}$")

ZIP_REGEX = re.compile(r"^\d{5}(-\d{4})?$")
STATE_CODES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
}

EMPLOYMENT_TYPES = {
    "salaried",
    "self_employed",
    "retired",
    "unemployed"
}

class ApplicantStatusEnum(str, Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"

