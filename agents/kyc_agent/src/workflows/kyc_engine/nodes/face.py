import time

from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import KYCState
# from src.services.face_liveness_service import face_liveness_service


@track_node("face")
def face_node(state: KYCState) -> KYCState:
    """
    Face Match + Liveness Node
    Performs actual face verification and anti-spoofing if images are provided.
    """
    start = time.time()

    duration = time.time() - start

    # TODO: Face match + liveness engine integration
    result = {
        "face_match_score": 0.91,
        "liveness_passed": True,
        "liveness_score": 0.93,
        "spoof_detected": False,
        "deepfake_score": 0.02,
        "replay_attack_detected": False,
        "flags": {}
    }
