import time
from src.workflows.kyc_engine.kyc_state import KYCState
from src.services.face_liveness_service import face_liveness_service


def face_node(state: KYCState) -> KYCState:
    """
    Face Match + Liveness Node
    Performs actual face verification and anti-spoofing if images are provided.
    """
    start = time.time()

    raw_req = state.get("raw_request", {})
    selfie = raw_req.get("selfie_image")
    id_card = raw_req.get("id_card_image")

    if selfie and id_card:
        # face_liveness_service is synchronous as it performs heavy CPU/GPU tasks
        result = face_liveness_service.verify_and_check_liveness(selfie, id_card)
    else:
        result = {
            "face_match_score": 0.0,
            "liveness_passed": False,
            "liveness_score": 0.0,
            "spoof_detected": False,
            "flags": {"MISSING_IMAGES": "Selfie or ID card image missing"}
        }

    duration = time.time() - start

    return {
        "face_check": result,
        "parallel_tasks_completed": ["face"],
        "node_execution_times": {"face": duration}
    }