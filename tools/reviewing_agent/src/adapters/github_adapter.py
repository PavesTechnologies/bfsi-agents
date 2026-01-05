import os
import json
import urllib.request
import urllib.error
from typing import List
from pathlib import Path

from domain.rules.base import Finding
from core.config import REPO_ROOT


# -----------------------------
# Helpers
# -----------------------------




def render_llm_insight(file: str, insight: dict) -> str:
    return (
        f"- **{insight['issue']}**\n"
        f"  - File: `{file}`\n"
        f"  - Suggested change: {insight['action']}\n"
    )


# -----------------------------
# Summary comment (PR-level)
# -----------------------------

def post_summary_comment(
    findings: List[Finding],
    llm_insights: List[dict] | None = None,
) -> None:
    if not findings and not llm_insights:
        return

    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GITHUB_TOKEN")

    if not event_path or not token:
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    pr = event.get("pull_request")
    if not pr:
        return

    repo = event["repository"]["full_name"]
    pr_number = pr["number"]

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "reviewing-agent",
    }

    body = "## 🤖 Reviewing Agent Findings\n\n"

    # ---- Deterministic rule findings ----
    if findings:
        for f in findings:
            body += f"- **{f.severity} {f.rule_id}**: {f.message}\n"
            if f.file:
                body += f"  - File: `{f.file}`\n"
            if f.suggestion:
                body += f"  - 💡 {f.suggestion}\n"
            body += "\n"

    # ---- LLM insights (controlled rendering) ----
    if llm_insights:
        body += "\n### LLM Suggestions\n\n"
        for insight in llm_insights:
            body += render_llm_insight(insight["file"], insight)
            body += "\n"

    payload = json.dumps({"body": body}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            response.read()
    except urllib.error.HTTPError:
        pass  # Non-blocking by design


# -----------------------------
# Inline PR comments (best effort)
# -----------------------------

def post_pr_comments(findings: List[Finding]) -> None:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GITHUB_TOKEN")

    if not event_path or not token:
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    pull_request = event.get("pull_request")
    if not pull_request:
        return

    repo = event["repository"]["full_name"]
    pr_number = pull_request["number"]
    commit_id = pull_request["head"]["sha"]

    api_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "reviewing-agent",
    }

    for finding in findings:
        if not finding.file or not finding.line:
            continue  # inline comments REQUIRE line numbers

        body = f"**{finding.severity} – {finding.rule_id}**\n\n{finding.message}"
        if finding.suggestion:
            body += f"\n\n💡 **Suggestion:** {finding.suggestion}"

        payload = {
            "body": body,
            "commit_id": commit_id,
            "path": finding.file,
            "side": "RIGHT",
            "line": finding.line,
        }

        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as response:
                response.read()
        except urllib.error.HTTPError:
            pass  # Non-blocking
