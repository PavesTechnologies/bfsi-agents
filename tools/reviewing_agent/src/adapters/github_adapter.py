import os
import json
import urllib.request
from typing import List

from pathlib import Path

from domain.rules.base import Finding
from core.config import REPO_ROOT


def to_repo_relative(path: str | None) -> str | None:
    if not path:
        return None

    try:
        file_path = Path(path)
        return str(file_path.relative_to(REPO_ROOT))
    except Exception:
        return path



def post_summary_comment(
    findings: List[Finding],
    llm_insights: list | None = None,
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

    # ---- Rule findings ----
    if findings:
        for f in findings:
            body += f"- **{f.severity} {f.rule_id}**: {f.message}\n"
            if f.file:
                body += f"  - File: `{to_repo_relative(f.file)}`\n"
            if f.suggestion:
                body += f"  - 💡 {f.suggestion}\n"
            body += "\n"

    # ---- LLM insights ----
    if llm_insights:
        body += "\n---\n\n### 🧠 LLM Architectural Insights\n\n"
        for insight in llm_insights:
            body += f"- **{insight.rule_id}**\n"
            body += f"  - File: `{to_repo_relative(insight.file)}`\n"
            body += f"  - {insight.explanation}\n\n"

    payload = json.dumps({"body": body}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    urllib.request.urlopen(req).read()


def post_pr_comments(findings: List[Finding]) -> None:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GITHUB_TOKEN")

    REPO_ROOT = Path(__file__).resolve().parents[3]

    if not event_path or not token:
        print("ℹ️ Not running in PR context or missing token")
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    pull_request = event.get("pull_request")
    if not pull_request:
        print("ℹ️ Not a pull request event")
        return

    repo = event["repository"]["full_name"]   # owner/repo
    pr_number = pull_request["number"]
    commit_id = pull_request["head"]["sha"]

    api_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "reviewing-agent",
    }

    print(f"📝 Posting {len(findings)} PR comments to {repo} PR #{pr_number}")
    for finding in findings:
        print(f"  → {finding}")


    for finding in findings:
        if not finding.file or not finding.line:
            continue  # inline comments REQUIRE line numbers

        file_path = Path(finding.file)

        try:
            relative_path = file_path.relative_to(REPO_ROOT)
        except ValueError:
            continue

        body = f"**{finding.severity} – {finding.rule_id}**\n\n{finding.message}"
        if finding.suggestion:
            body += f"\n\n💡 **Suggestion:** {finding.suggestion}"

        payload = {
            "body": body,
            "commit_id": commit_id,
            "path": str(relative_path),
            "side": "RIGHT",
            "line": finding.line,
        }

        print(f"📝 Adding comment to {finding.file}:{finding.line}: {finding.message}")
        print(payload)

        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as response:
                response.read()
        except urllib.error.HTTPError as e:
            print(f"⚠️ Failed to post comment: {e.code} {e.reason}")
