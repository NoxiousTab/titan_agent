from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from integrations.jira import create_jira_issue
from integrations.n8n import trigger_n8n
from models import Ticket


def _priority_from_severity(severity: str) -> str:
    if severity == "P1":
        return "Highest"
    if severity == "P2":
        return "High"
    if severity == "P3":
        return "Medium"
    return "Low"


def escalate_if_needed(db: Session, ticket: Ticket) -> Ticket:
    if ticket.severity != "P1":
        return ticket

    ticket.escalated = True

    labels: List[str] = ["escalated"]
    if ticket.is_duplicate:
        labels.append("duplicate")

    jira_key = create_jira_issue(
        summary=f"[{ticket.severity}] {ticket.title}",
        description=ticket.description,
        priority=_priority_from_severity(ticket.severity),
        labels=labels,
    )
    ticket.jira_issue_key = jira_key

    trigger_n8n(
        {
            "ticket_id": ticket.id,
            "severity": ticket.severity,
            "assigned_team": ticket.assigned_team,
            "escalated": ticket.escalated,
            "jira_issue_key": ticket.jira_issue_key,
        }
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
