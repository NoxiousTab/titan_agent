from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests


def _configured() -> bool:
    return all(
        os.getenv(k, "").strip() for k in ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
    )


def create_jira_issue(
    summary: str,
    description: str,
    priority: str,
    labels: List[str],
) -> Optional[str]:
    if not _configured():
        return "MOCK-TRIAGE-1"

    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "")
    project = os.getenv("JIRA_PROJECT_KEY", "")

    url = f"{base_url}/rest/api/3/issue"
    payload: Dict[str, Any] = {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
            "issuetype": {"name": "Task"},
            "priority": {"name": priority},
            "labels": labels,
        }
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            auth=(email, token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code >= 300:
            return "MOCK-TRIAGE-1"
        data = resp.json()
        return data.get("key") or "MOCK-TRIAGE-1"
    except Exception:
        return "MOCK-TRIAGE-1"
