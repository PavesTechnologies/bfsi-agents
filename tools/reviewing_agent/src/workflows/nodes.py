from core.config import LOCAL_DEV
from adapters.git_adapter import get_changed_files
from domain.signals.aggregator import collect_signals
from services.rule_engine import run_rules
from services.signal_engine import filter_llm_eligible_signals
from services.review_service import run_llm_review
from adapters.github_adapter import (
    post_inline_llm_comments,
    post_summary_comment,
)
from reporters.console_reporter import print_summary
from .review_state import ReviewState


def fetch_changed_files(_: ReviewState):
    files = get_changed_files()
    return {"changed_files": files}


def run_rule_engine(state: ReviewState):
    findings = run_rules(state["changed_files"])
    return {"findings": findings}


def collect_and_filter_signals(state: ReviewState):
    signals = collect_signals(state["changed_files"])
    signals = filter_llm_eligible_signals(signals)
    return {"signals": signals}


def run_llm(state: ReviewState):
    insights = run_llm_review(state["signals"])
    return {"llm_insights": insights}


def report(state: ReviewState):
    findings = state.get("findings", [])
    llm_insights = state.get("llm_insights", [])

    print_summary(findings, llm_insights)

    if not LOCAL_DEV:
        post_summary_comment(findings, llm_insights)
        post_inline_llm_comments(llm_insights)

    return {}
