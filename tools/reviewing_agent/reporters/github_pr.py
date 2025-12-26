import os
import json
import requests
from typing import List
from rules.base import Finding


def post_pr_comments(findings: List[Finding]) -> None:
    """
    Posts inline PR comments for each finding.
    No-op if not running in a PR context.
    """

    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GITHUB_TOKEN")

    if not event_path or not token:
        print("ℹ️ Not running in PR context or missing token")
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    pull_request = event.get("pull_request")
    if not pull_request:
        print("ℹ️ Not a pull request event")
        return

    repo = event["repository"]["full_name"]
    pr_number = pull_request["number"]
    commit_id = pull_request["head"]["sha"]

    api_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    for finding in findings:
        if not finding.file:
            continue

        body = f"**{finding.severity} – {finding.rule_id}**\n\n{finding.message}"
        if finding.suggestion:
            body += f"\n\n💡 **Suggestion:** {finding.suggestion}"

        payload = {
            "body": body,
            "commit_id": commit_id,
            "path": finding.file,
            "side": "RIGHT",
        }

        # Inline comment only if line is available
        if finding.line:
            payload["line"] = finding.line

        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code >= 300:
            print(
                f"⚠️ Failed to post comment for {finding.file}: "
                f"{response.status_code} {response.text}"
            )
