import os
import json
import urllib.request
from typing import List
from rules.base import Finding


def post_summary_comment(findings: List[Finding]) -> None:
    if not findings:
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

    for f in findings:
        body += f"- **{f.severity} {f.rule_id}**: {f.message}\n"
        if f.file:
            body += f"  - File: `{f.file}`\n"
        if f.suggestion:
            body += f"  - 💡 {f.suggestion}\n"

    payload = json.dumps({"body": body}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    urllib.request.urlopen(req).read()
