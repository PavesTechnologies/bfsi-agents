
# from adapters.git_adapter import get_changed_files
# from adapters.github_adapter import post_inline_llm_comments, post_pr_comments, post_summary_comment
# from core.config import LOCAL_DEV
# from domain.signals.aggregator import collect_signals
# from reporters.console_reporter import print_report, print_summary
# from services.review_service import run_llm_review
# from services.rule_engine import run_rules
# from services.signal_engine import filter_llm_eligible_signals


# def run_review_workflow():
#     print("Reviewing Agent started")

#     changed_files = get_changed_files()
#     if not changed_files:
#         print("ℹ️ No changed files detected")
#         return

#     findings = run_rules(changed_files)

#     llm_insights = []
#     signals = collect_signals(changed_files)
#     signals = filter_llm_eligible_signals(signals)

#     if signals:
#         llm_insights = run_llm_review(signals)

#         # print_report(findings)
#     print_summary(findings, llm_insights)
#     if not LOCAL_DEV:
#         post_summary_comment(findings, llm_insights)
#         # post_pr_comments(findings)
#         post_inline_llm_comments(llm_insights)


#     print("Reviewing Agent finished (non-blocking)")


from langgraph.graph import StateGraph, END
from .debug import debug_node
from .review_state import ReviewState
from .nodes import (
    fetch_changed_files,
    run_rule_engine,
    collect_and_filter_signals,
    run_llm,
    report,
)
from .guards import should_call_llm


def build_review_graph():
    graph = StateGraph(ReviewState)

    DEBUG_GRAPH = False

    graph.add_node("fetch_files_node", debug_node("fetch_changed_files",fetch_changed_files) if DEBUG_GRAPH else fetch_changed_files)
    graph.add_node("rules_node", debug_node("run_rule_engine",run_rule_engine) if DEBUG_GRAPH else run_rule_engine)
    graph.add_node("signals_node", debug_node("collect_and_filter_signals",collect_and_filter_signals) if DEBUG_GRAPH else collect_and_filter_signals)
    graph.add_node("llm_node", debug_node("run_llm",run_llm) if DEBUG_GRAPH else run_llm)
    graph.add_node("report_node", debug_node("report",report) if DEBUG_GRAPH else report)

    graph.set_entry_point("fetch_files_node")

    graph.add_edge("fetch_files_node", "rules_node")
    graph.add_edge("rules_node", "signals_node")

    graph.add_conditional_edges(
        "signals_node",
        should_call_llm,
        {
            "llm_node": "llm_node",
            "report_node": "report_node",
        },
    )

    graph.add_edge("llm_node", "report_node")
    graph.add_edge("report_node", END)

    return graph.compile()
