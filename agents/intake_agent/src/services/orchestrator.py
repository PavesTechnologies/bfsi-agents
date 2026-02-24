"""
Workflow Orchestrator
"""

from src.repositories.idempotency_repository import IdempotencyRepository
from src.workflows.decision_flow import build_graph

_graph = build_graph()


def run_agent(input_text: str) -> dict:
    final_state = _graph.invoke(
        {
            "context": {"input_text": input_text},
            "retries": 0,
        }
    )
    return final_state["context"]


async def process_intake_job(request_id, payload, db):
    repo = IdempotencyRepository(db)

    await repo.mark_processing(request_id)

    try:
        # 🔹 ACTUAL intake logic later
        result = {"request_id": str(request_id), "status": "success"}

        await repo.mark_completed(request_id, result)

    except Exception:
        await repo.mark_failed(request_id)
        raise
