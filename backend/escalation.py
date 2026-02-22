from __future__ import annotations

import os
import requests
import logging

from sqlalchemy.orm import Session
from models import Ticket

logger = logging.getLogger(__name__)

def escalate_if_needed(db: Session, ticket: Ticket, ai_reasoning: str = "") -> Ticket:
    """
    Route tickets to the appropriate n8n ESB Workflow based on severity.
    - P1/P2 -> esb-hitl-intake (Workflow 2: Slack Approval -> Jira)
    - P3/P4 -> esb-intake (Workflow 1: Direct Jira Creation)
    """
    payload = {
        "ticket_id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "reporter": ticket.reporter,
        "department": ticket.department,
        "severity": ticket.severity,
        "confidence": ticket.confidence,
        "assigned_team": ticket.assigned_team,
        "suggested_fixes": ticket.suggested_fixes,
        "is_duplicate": ticket.is_duplicate,
        "duplicate_ticket_id": ticket.duplicate_ticket_id,
        "similarity_score": ticket.similarity_score,
        "ai_reasoning": ai_reasoning,
        "escalated": False,
    }

    if ticket.severity in ["P1", "P2"]:
        ticket.escalated = True
        ticket.lifecycle_status = "ESCALATED"
        payload["escalated"] = True
        
        # Save the escalation state
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        # Use environment variable for HITL webhook, defaulting to localhost if not set
        target_webhook = os.getenv("N8N_HITL_WEBHOOK_URL", "http://localhost:5678/webhook-test/esb-hitl-intake").strip()
        logger.info(f"Routing P{ticket.severity[-1]} Ticket #{ticket.id} to HITL Workflow 2")
    else:
        target_webhook = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook-test/esb-intake").strip()
        logger.info(f"Routing P{ticket.severity[-1]} Ticket #{ticket.id} to Standard Workflow 1")

    try:
        resp = requests.post(target_webhook, json=payload, timeout=15)
        if resp.status_code >= 300:
            logger.error(f"Failed to trigger ESB ({target_webhook}): HTTP {resp.status_code}")
        else:
            logger.info(f"Successfully triggered ESB {target_webhook}")
    except Exception as e:
        logger.error(f"Error triggering ESB: {e}")

    return ticket
