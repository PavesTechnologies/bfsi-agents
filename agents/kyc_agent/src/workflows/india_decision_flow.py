"""
India KYC Agent – LangGraph Decision Flow

Graph topology (Sprint 2 plan):
  normalize_india
    ├── aadhaar_pan  → video_kyc → face_dedup  (sequential chain)
    ├── aml_india                               (parallel)
    ├── contact_india                           (parallel)
    └── address_india                           (parallel)
  All four branches → risk_india → ckyc_upload → explanation_india → END
"""

from langgraph.graph import END, StateGraph

from src.workflows.kyc_engine.india_kyc_state import IndianKYCState
from src.workflows.kyc_engine.nodes.normalize_india import normalize_india_node
from src.workflows.kyc_engine.nodes.aadhaar_pan import aadhaar_pan_node
from src.workflows.kyc_engine.nodes.video_kyc import video_kyc_node
from src.workflows.kyc_engine.nodes.face_dedup import face_dedup_node
from src.workflows.kyc_engine.nodes.aml_india import aml_india_node
from src.workflows.kyc_engine.nodes.contact_india import contact_india_node
from src.workflows.kyc_engine.nodes.address_india import address_india_node
from src.workflows.kyc_engine.nodes.risk_india import risk_india_node
from src.workflows.kyc_engine.nodes.ckyc_upload import ckyc_upload_node
from src.workflows.kyc_engine.nodes.explanation_india import explanation_india_node

# Reuse the pool and checkpointer that app.py opens at startup via decision_flow.py.
# Creating a second pool here would leave it unopened and crash at runtime.
from src.workflows.decision_flow import connection_pool, checkpointer


def build_india_graph():
    graph = StateGraph(IndianKYCState)

    graph.add_node("normalize_india", normalize_india_node)
    graph.add_node("aadhaar_pan", aadhaar_pan_node)
    graph.add_node("video_kyc", video_kyc_node)
    graph.add_node("face_dedup", face_dedup_node)
    graph.add_node("aml_india", aml_india_node)
    graph.add_node("contact_india", contact_india_node)
    graph.add_node("address_india", address_india_node)
    graph.add_node("risk_india", risk_india_node)
    graph.add_node("ckyc_upload", ckyc_upload_node)
    graph.add_node("explanation_india", explanation_india_node)

    graph.set_entry_point("normalize_india")

    # Parallel fan-out from normalize
    graph.add_edge("normalize_india", "aadhaar_pan")
    graph.add_edge("normalize_india", "aml_india")
    graph.add_edge("normalize_india", "contact_india")
    graph.add_edge("normalize_india", "address_india")

    # Sequential Aadhaar identity chain
    graph.add_edge("aadhaar_pan", "video_kyc")
    graph.add_edge("video_kyc", "face_dedup")

    # Fan-in to risk aggregator
    graph.add_edge("face_dedup", "risk_india")
    graph.add_edge("aml_india", "risk_india")
    graph.add_edge("contact_india", "risk_india")
    graph.add_edge("address_india", "risk_india")

    # Post-aggregate pipeline
    graph.add_edge("risk_india", "ckyc_upload")
    graph.add_edge("ckyc_upload", "explanation_india")
    graph.add_edge("explanation_india", END)

    return graph.compile(checkpointer=checkpointer)
