"""
Mock Face Deduplication Adapter.

Uses an in-memory seeded registry of known applicant IDs to simulate
face vector DB lookups (Pinecone / pgvector in production).

Scenario trigger (first 4 digits of Aadhaar):
  5555 → duplicate found, matched against seeded record APP-EXISTING-001
  Default → no duplicate; applicant registered in registry
"""

from src.workflows.kyc_engine.india_kyc_state import FaceDeduplicationState

_SEEDED_KNOWN_FACES: dict[str, str] = {
    "APP-EXISTING-001": "Ravi Kumar",
    "APP-EXISTING-002": "Priya Sharma",
    "APP-EXISTING-003": "Amit Singh",
}


class MockFaceDedupAdapter:
    """
    Mock face deduplication adapter.

    Scenario triggers (Aadhaar first 4 digits):
      5555 → forced duplicate match against APP-EXISTING-001 (similarity 0.93)
      Default → no duplicate; applicant added to registry
    """

    def __init__(self):
        self._registry: dict[str, str] = dict(_SEEDED_KNOWN_FACES)

    def check_duplicate(self, applicant_id: str, aadhaar_prefix: str) -> FaceDeduplicationState:
        if aadhaar_prefix == "5555":
            match_id = "APP-EXISTING-001"
            return FaceDeduplicationState(
                is_duplicate=True,
                matching_applicant_ids=[match_id],
                highest_similarity=0.93,
                flags={"FACE_DEDUP_ALERT": f"Face matches existing customer record {match_id} (similarity 0.93)"},
            )

        self._registry[applicant_id] = applicant_id
        return FaceDeduplicationState(
            is_duplicate=False,
            matching_applicant_ids=[],
            highest_similarity=0.0,
            flags={},
        )
