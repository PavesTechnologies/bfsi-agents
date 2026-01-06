
from adapters.git_adapter import get_changed_files
from adapters.github_adapter import post_inline_llm_comments, post_pr_comments, post_summary_comment
from core.config import LOCAL_DEV
from domain.signals.aggregator import collect_signals
from reporters.console_reporter import print_report, print_summary
from services.review_service import run_llm_review
from services.rule_engine import run_rules
from services.signal_engine import filter_llm_eligible_signals


def run_review_workflow():
    print("Reviewing Agent started")

    changed_files = get_changed_files()
    if not changed_files:
        print("ℹ️ No changed files detected")
        return

    findings = run_rules(changed_files)

    llm_insights = []
    signals = collect_signals(changed_files)
    signals = filter_llm_eligible_signals(signals)

    if signals:
        llm_insights = run_llm_review(signals)

    if LOCAL_DEV:
        # print_report(findings)
        print_summary(findings, llm_insights)
    else:
        post_summary_comment(findings, llm_insights)
        # post_pr_comments(findings)
        post_inline_llm_comments(llm_insights)


    print("Reviewing Agent finished (non-blocking)")
