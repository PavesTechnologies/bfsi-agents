from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Job:
    job_id: UUID
    request_id: UUID
    job_type: str  # e.g. "intake"
    payload: dict
