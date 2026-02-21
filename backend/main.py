from __future__ import annotations

import os
from collections import Counter
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from ai_engine import triage_ticket
from database import Base, engine, get_db
from escalation import escalate_if_needed
from models import Ticket
from schemas import DashboardMetrics, SeedResponse, TicketCreate, TicketOut
from seed import seed_demo_tickets
from similarity import detect_duplicate

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Incident Triage Agent",
    version="1.0.0",
    description="Enterprise-grade AI triage for IT support tickets (severity, routing, duplicates, escalation, Jira, n8n).",
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_out(ticket: Ticket, ai_reasoning: Optional[str] = None) -> TicketOut:
    return TicketOut(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        reporter=ticket.reporter,
        department=ticket.department,
        severity=ticket.severity,
        confidence=ticket.confidence,
        assigned_team=ticket.assigned_team,
        suggested_fixes=ticket.suggested_fixes,
        is_duplicate=ticket.is_duplicate,
        duplicate_ticket_id=ticket.duplicate_ticket_id,
        similarity_score=ticket.similarity_score,
        escalated=ticket.escalated,
        jira_issue_key=ticket.jira_issue_key,
        created_at=ticket.created_at,
        ai_reasoning=ai_reasoning,
    )


@app.get("/tickets", response_model=List[TicketOut])
def list_tickets(db: Session = Depends(get_db)) -> List[TicketOut]:
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    return [_to_out(t) for t in tickets]


@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> TicketOut:
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _to_out(t)


@app.post("/tickets", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> TicketOut:
    ai = triage_ticket(payload.title, payload.description)

    is_dup, dup_id, sim = detect_duplicate(db, payload.title, payload.description, threshold=0.85)

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        reporter=payload.reporter,
        department=payload.department,
        severity=ai["severity"],
        confidence=float(ai["confidence"]),
        assigned_team=ai["assigned_team"],
        suggested_fixes=ai["suggested_fixes"],
        is_duplicate=bool(is_dup),
        duplicate_ticket_id=dup_id,
        similarity_score=float(sim),
        escalated=False,
        jira_issue_key=None,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    ticket = escalate_if_needed(db, ticket)

    return _to_out(ticket, ai_reasoning=str(ai.get("reasoning", "")))


@app.get("/dashboard/metrics", response_model=DashboardMetrics)
def dashboard_metrics(db: Session = Depends(get_db)) -> DashboardMetrics:
    tickets = db.query(Ticket).all()

    total = len(tickets)
    escalated = sum(1 for t in tickets if t.escalated)
    duplicates = sum(1 for t in tickets if t.is_duplicate)

    severity_counts = Counter([t.severity for t in tickets])
    team_counts = Counter([t.assigned_team for t in tickets])

    by_severity = [{"name": k, "value": int(v)} for k, v in sorted(severity_counts.items())]
    by_team = [{"name": k, "value": int(v)} for k, v in sorted(team_counts.items())]

    return DashboardMetrics(
        total_tickets=total,
        escalated_tickets=escalated,
        duplicate_tickets=duplicates,
        by_severity=by_severity,
        by_team=by_team,
    )


@app.post("/seed", response_model=SeedResponse)
def seed(db: Session = Depends(get_db)) -> SeedResponse:
    inserted = seed_demo_tickets(db)
    return SeedResponse(inserted=inserted)
