from __future__ import annotations

from typing import Dict, List

from sqlalchemy.orm import Session

from models import Ticket


def seed_demo_tickets(db: Session) -> int:
    existing = db.query(Ticket).count()
    if existing >= 10:
        return 0

    tickets: List[Dict] = [
        {
            "title": "Production API returning 503 - checkout service down",
            "description": "Production down: users cannot complete checkout. 503 from /checkout. Started 10 minutes ago.",
            "reporter": "SRE Oncall",
            "department": "E-Commerce",
        },
        {
            "title": "System outage: Customer portal unavailable",
            "description": "System outage observed across regions. Portal login fails for all users. production down.",
            "reporter": "NOC",
            "department": "Customer Experience",
        },
        {
            "title": "VPN not connecting for multiple users",
            "description": "VPN tunnel fails with authentication error. Many remote employees unable to connect since morning.",
            "reporter": "IT Helpdesk",
            "department": "Corporate IT",
        },
        {
            "title": "Duplicate: VPN connection failing with auth error",
            "description": "Several users report VPN not connecting. Error says authentication failed. Started today 9AM.",
            "reporter": "Service Desk",
            "department": "Corporate IT",
        },
        {
            "title": "Potential data breach - suspicious access to finance share",
            "description": "Possible data breach: unusual downloads detected from finance share, unauthorized account activity. security incident.",
            "reporter": "SOC Analyst",
            "department": "Security",
        },
        {
            "title": "Database performance degradation - slow queries on orders DB",
            "description": "Orders DB experiencing slow queries and increased lock waits. Degraded performance for reporting jobs.",
            "reporter": "DBA",
            "department": "Data Platform",
        },
        {
            "title": "Password reset request - user locked out",
            "description": "User cannot login due to repeated failed attempts. Needs password reset and MFA re-enrollment.",
            "reporter": "HR Ops",
            "department": "HR",
        },
        {
            "title": "High network latency between HQ and DC",
            "description": "Intermittent high latency and packet loss observed on WAN link between HQ and data center.",
            "reporter": "Network Ops",
            "department": "Infrastructure",
        },
        {
            "title": "App error: 500 when submitting expense reports",
            "description": "Expense app throws 500 on submit for a subset of users. Workaround: save draft works.",
            "reporter": "Finance Ops",
            "department": "Finance",
        },
        {
            "title": "Mobile app crash on launch after latest update",
            "description": "After the latest app update, some Android devices crash on launch. Single user reported so far.",
            "reporter": "Product Support",
            "department": "Product",
        },
    ]

    inserted = 0
    for t in tickets:
        ticket = Ticket(
            title=t["title"],
            description=t["description"],
            reporter=t["reporter"],
            department=t["department"],
            severity="P4",
            confidence=0.5,
            assigned_team="Application Support",
            suggested_fixes=[],
            is_duplicate=False,
            duplicate_ticket_id=None,
            similarity_score=0.0,
            escalated=False,
            jira_issue_key=None,
        )
        db.add(ticket)
        inserted += 1

    db.commit()
    return inserted
