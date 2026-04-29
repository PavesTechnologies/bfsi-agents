"""
Mock Video KYC (V-CIP) Adapter.

Simulates a V-CIP provider (Signzy / HyperVerge / IDfy interface):
  - initiate_session: creates a session, returns session_id + mock URLs
  - get_session_result: returns outcome driven by Aadhaar prefix

Scenario triggers (first 4 digits of Aadhaar):
  6660 → FAILED – liveness check score below threshold
  6661 → FAILED – geo-location detected outside India
  Default → COMPLETED (full pass, all RBI V-CIP requirements met)
"""

import uuid

from src.workflows.kyc_engine.india_kyc_state import VideoKYCState


class MockVideoKYCAdapter:
    """
    Mock V-CIP adapter.

    Scenario triggers (Aadhaar first 4 digits):
      6660 → liveness failed
      6661 → geo outside India
      Default → success
    """

    def initiate_session(self, applicant_id: str) -> dict[str, str]:
        session_id = str(uuid.uuid4())
        return {
            "session_id": session_id,
            "customer_url": f"mock://vcip/session/{session_id}",
            "agent_url": f"mock://vcip/agent/{session_id}",
            "status": "INITIATED",
        }

    def get_session_result(self, session_id: str, aadhaar_prefix: str) -> VideoKYCState:
        if aadhaar_prefix == "6660":
            return VideoKYCState(
                session_id=session_id,
                status="FAILED",
                liveness_score=0.42,
                face_match_score=0.0,
                geo_within_india=True,
                geo_location={"lat": 28.6139, "lon": 77.2090},
                consent_recorded=True,
                ovd_captured=False,
                failure_reason="Liveness detection score below minimum threshold (0.60)",
                flags={"LIVENESS_FAILED": "Passive liveness score 0.42 is below required 0.60"},
            )

        if aadhaar_prefix == "6661":
            return VideoKYCState(
                session_id=session_id,
                status="FAILED",
                liveness_score=0.91,
                face_match_score=0.0,
                geo_within_india=False,
                geo_location={"lat": 51.5074, "lon": -0.1278},
                consent_recorded=True,
                ovd_captured=False,
                failure_reason="Geo-location outside India boundaries",
                flags={"GEO_OUTSIDE_INDIA": "Applicant location lat=51.5074 lon=-0.1278 is outside India"},
            )

        return VideoKYCState(
            session_id=session_id,
            status="COMPLETED",
            liveness_score=0.97,
            face_match_score=0.94,
            geo_within_india=True,
            geo_location={"lat": 28.6139, "lon": 77.2090},
            consent_recorded=True,
            ovd_captured=True,
            failure_reason=None,
            flags={},
        )
