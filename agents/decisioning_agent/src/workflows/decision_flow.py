"""
Underwriting Agent - Parallel Execution Graph

Architecture:
- Intake / Normalize
- Parallel Risk Evaluation
- Deterministic Aggregation
- Deterministic Decision
- Conditional Routing (Approve / Counter Offer / Human Review / Decline)
"""

import json

from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from psycopg_pool import AsyncConnectionPool

from src.core.config import get_settings
from src.workflows.decision_engine.nodes.behavior_node import behavior_node
from src.workflows.decision_engine.nodes.counter_offer_node import counter_offer_node
from src.workflows.decision_engine.nodes.credit_score_node import credit_score_node
from src.workflows.decision_engine.nodes.decision_llm_node import decision_llm_node
from src.workflows.decision_engine.nodes.exposure_node import exposure_node
from src.workflows.decision_engine.nodes.final_response_node import final_response_node
from src.workflows.decision_engine.nodes.human_review_packet_node import (
    human_review_packet_node,
)
from src.workflows.decision_engine.nodes.income_node import income_node
from src.workflows.decision_engine.nodes.inquiry_node import inquiry_node
from src.workflows.decision_engine.nodes.pi_deletion_node import pi_deletion_node
from src.workflows.decision_engine.nodes.public_record_node import public_record_node
from src.workflows.decision_engine.nodes.risk_aggregator_node import (
    risk_aggregator_node,
)
from src.workflows.decision_engine.nodes.utilization_node import utilization_node
from src.workflows.decision_state import LoanApplicationState

settings = get_settings()
load_dotenv()
DB_URI = settings.DATABASE_GENERIC
connection_pool = AsyncConnectionPool(conninfo=DB_URI, min_size=1, max_size=2, open=False)
checkpointer = AsyncPostgresSaver(connection_pool)


def build_underwriting_graph():
    graph = StateGraph(LoanApplicationState)

    graph.add_node("pi_deletion", pi_deletion_node)
    graph.add_node("credit_score", credit_score_node)
    graph.add_node("public_record", public_record_node)
    graph.add_node("credit_utilization", utilization_node)
    graph.add_node("debt_exposure", exposure_node)
    graph.add_node("payment_behavior", behavior_node)
    graph.add_node("inquiry", inquiry_node)
    graph.add_node("income_analysis", income_node)
    graph.add_node("aggregate", risk_aggregator_node)
    graph.add_node("decision", decision_llm_node)
    graph.add_node("counter_offer", counter_offer_node)
    graph.add_node("human_review_packet", human_review_packet_node)
    graph.add_node("final_response", final_response_node)

    graph.set_entry_point("pi_deletion")

    graph.add_edge("pi_deletion", "credit_score")
    graph.add_edge("pi_deletion", "public_record")
    graph.add_edge("pi_deletion", "credit_utilization")
    graph.add_edge("pi_deletion", "debt_exposure")
    graph.add_edge("pi_deletion", "payment_behavior")
    graph.add_edge("pi_deletion", "inquiry")
    graph.add_edge("pi_deletion", "income_analysis")

    graph.add_edge("credit_score", "aggregate")
    graph.add_edge("public_record", "aggregate")
    graph.add_edge("credit_utilization", "aggregate")
    graph.add_edge("debt_exposure", "aggregate")
    graph.add_edge("payment_behavior", "aggregate")
    graph.add_edge("inquiry", "aggregate")
    graph.add_edge("income_analysis", "aggregate")

    graph.add_edge("aggregate", "decision")

    def route_after_decision(state: LoanApplicationState):
        decision = state.get("decision_result", {}).get("decision")
        if decision == "COUNTER_OFFER":
            return "counter_offer"
        if decision == "REFER_TO_HUMAN":
            return "human_review_packet"
        return "final_response"

    graph.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "counter_offer": "counter_offer",
            "human_review_packet": "human_review_packet",
            "final_response": "final_response",
        },
    )

    graph.add_edge("counter_offer", "final_response")
    graph.add_edge("human_review_packet", "final_response")
    graph.add_edge("final_response", END)

    workflow = graph.compile(checkpointer=checkpointer)
    workflow.pool = connection_pool
    workflow.checkpointer = checkpointer
    return workflow


if __name__ == "__main__":
    workflow = build_underwriting_graph()

    with open(r"src\workflows\exp-prequal-fico9.json", "r", encoding="utf-8") as f:
        experian_payload = json.load(f)

    data = {
        "application_id": "APP_001",
        "raw_experian_data": experian_payload,
        "user_request": {
            "amount": 100000,
            "tenure": 20,
        },
        "bank_statement_summary": {
            "monthly_income": 10000,
        },
    }

    result = workflow.invoke(data)
    print("Final Decision:")
    print(result)
