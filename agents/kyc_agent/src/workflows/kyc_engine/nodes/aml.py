"""
AML / OFAC Screening Node
"""

import time

from src.core.telemetry import track_node
from src.workflows.kyc_engine.kyc_state import KYCState


@track_node("aml")
def aml_node(state: KYCState) -> KYCState:
    start = time.time()

    # TODO: OFAC / sanctions vendor integration
    result = {
        "ofac_match": False,
        "ofac_confidence": 0.0,
        "pep_match": False,
        "sanctions_list_version": "2026-01",
        "aml_score": 0.05,
        "flags": {},
    }

    duration = time.time() - start

    return {
        "aml_check": result,
        "parallel_tasks_completed": ["aml"],
        "node_execution_times": {"aml": duration},
    }
