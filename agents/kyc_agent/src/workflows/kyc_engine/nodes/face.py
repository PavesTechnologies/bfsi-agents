"""
Face Match + Liveness Node
"""

import time

from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import KYCState


@track_node("face")
def face_node(state: KYCState) -> KYCState:
    start = time.time()

    # TODO: Face match + liveness engine integration
    result = {
        "face_match_score": 0.91,
        "liveness_passed": True,
        "liveness_score": 0.93,
        "spoof_detected": False,
        "deepfake_score": 0.02,
        "replay_attack_detected": False,
        "flags": {},
    }

    duration = time.time() - start

    return {
        "face_check": result,
        "parallel_tasks_completed": ["face"],
        "node_execution_times": {"face": duration},
    }
