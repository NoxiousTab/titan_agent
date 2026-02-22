from __future__ import annotations

import os
from collections import Counter
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from ai_engine import load_rulebook, triage_ticket
from database import Base, engine, get_db
from escalation import escalate_if_needed
from monitoring import MonitoringPayloadError, parse_datadog_alert
from models import Ticket
from schemas import DashboardMetrics, JiraClosureWebhook, SeedResponse, TicketCreate, TicketOut, TicketStatusUpdate
from seed import seed_demo_tickets
from similarity import detect_duplicate

load_dotenv()

Base.metadata.create_all(bind=engine)


def _migrate_sqlite() -> None:
    if not str(engine.url).startswith("sqlite"):
        return

    with engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(tickets)"))
        col_names = {row[1] for row in cols.fetchall()}
        if "lifecycle_status" not in col_names:
            conn.execute(
                text(
                    "ALTER TABLE tickets ADD COLUMN lifecycle_status VARCHAR(20) NOT NULL DEFAULT 'RECEIVED'"
                )
            )
            conn.commit()
        if "status" not in col_names:
            conn.execute(
                text("ALTER TABLE tickets ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'open'")
            )
            conn.commit()
        if "resolved_at" not in col_names:
            conn.execute(
                text("ALTER TABLE tickets ADD COLUMN resolved_at DATETIME")
            )
            conn.commit()

        if "source" not in col_names:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN source VARCHAR(30) NOT NULL DEFAULT 'manual'"))
            conn.commit()

        if "metadata" not in col_names:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN metadata JSON"))
            conn.commit()


_migrate_sqlite()

app = FastAPI(
    title="Smart Incident Triage Agent",
    version="2.0.0",
    description="Enterprise-grade AI triage for IT support tickets. V2 ESB architecture — n8n handles orchestration.",
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_out(ticket: Ticket, ai_reasoning: Optional[str] = None, decision_trace: Optional[Any] = None) -> TicketOut:
    return TicketOut(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        reporter=ticket.reporter,
        department=ticket.department,

        source=getattr(ticket, "source", "manual"),
        metadata=getattr(ticket, "alert_metadata", None),
        severity=ticket.severity,
        confidence=ticket.confidence,
        assigned_team=ticket.assigned_team,
        suggested_fixes=ticket.suggested_fixes,
        is_duplicate=ticket.is_duplicate,
        duplicate_ticket_id=ticket.duplicate_ticket_id,
        similarity_score=ticket.similarity_score,
        escalated=ticket.escalated,
        jira_issue_key=ticket.jira_issue_key,
        lifecycle_status=ticket.lifecycle_status,
        status=ticket.status,
        resolved_at=ticket.resolved_at,
        created_at=ticket.created_at,
        ai_reasoning=ai_reasoning,
        decision_trace=decision_trace,
    )


def _match_any(text_lower: str, phrases: list[str]) -> Optional[str]:
    for p in phrases:
        if p and str(p).lower() in text_lower:
            return str(p)
    return None


def _build_decision_trace(
    title: str,
    description: str,
    assigned_team: str,
    severity: str,
    similarity_score: float,
    escalated: bool,
    triage_source: Optional[str] = None,
) -> dict:
    rb = load_rulebook()
    text_lower = f"{title}\n{description}".lower()

    override_phrase = _match_any(text_lower, [str(x) for x in (rb.get("overrides", {}).get("p1_phrases", []) or [])])

    routing_rules = (rb.get("routing", {}) or {}).get("rules", {}) or {}
    routing_keywords = [str(x) for x in (routing_rules.get(assigned_team, []) or [])]
    routing_match = _match_any(text_lower, routing_keywords)

    signals = (rb.get("severity", {}) or {}).get("signals", {}) or {}
    severity_keywords = [str(x) for x in (signals.get(severity, []) or [])]
    severity_match = _match_any(text_lower, severity_keywords)

    if override_phrase:
        severity_logic = "P1 override"
        signals_detected = override_phrase
    elif severity_match:
        severity_logic = f"Matched {severity} signal"
        signals_detected = severity_match
    else:
        severity_logic = "AI classification"
        signals_detected = None

    return {
        "triage_source": triage_source,
        "signals_detected": signals_detected,
        "severity_logic": severity_logic,
        "routing_logic": f"Matched {assigned_team} keywords" if routing_match else f"Defaulted to {assigned_team}",
        "routing_match": routing_match,
        "duplicate_score": float(similarity_score),
        "escalation_triggered": bool(escalated),
    }


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
    reporter = (payload.reporter or "").strip() or "Unknown"
    department = (payload.department or "").strip() or "Unknown"
    ai = triage_ticket(payload.title, payload.description)

    is_dup, dup_id, sim = detect_duplicate(db, payload.title, payload.description, threshold=0.85)

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        reporter=reporter,
        department=department,
        severity=ai["severity"],
        confidence=float(ai["confidence"]),
        assigned_team=ai["assigned_team"],
        suggested_fixes=ai["suggested_fixes"],
        is_duplicate=bool(is_dup),
        duplicate_ticket_id=dup_id,
        similarity_score=float(sim),
        escalated=False,
        jira_issue_key=None,
        lifecycle_status="TRIAGED",
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    ai_reasoning_str = str(ai.get("reasoning", ""))
    ticket = escalate_if_needed(db, ticket, ai_reasoning=ai_reasoning_str)

    decision_trace = _build_decision_trace(
        title=ticket.title,
        description=ticket.description,
        assigned_team=ticket.assigned_team,
        severity=ticket.severity,
        similarity_score=ticket.similarity_score,
        escalated=ticket.escalated,
        triage_source=str(ai.get("triage_source", "")) or None,
    )

    return _to_out(ticket, ai_reasoning=str(ai.get("reasoning", "")), decision_trace=decision_trace)


@app.post("/monitoring/datadog", response_model=TicketOut)
async def ingest_datadog_alert(request: Request, db: Session = Depends(get_db)) -> TicketOut:
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON payload")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")

    try:
        title, description, metadata, force_p1 = parse_datadog_alert(payload)
    except MonitoringPayloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Datadog payload")

    try:
        ai = triage_ticket(title, description)
    except Exception:
        raise HTTPException(status_code=500, detail="Triage failed")

    if force_p1:
        ai = dict(ai)
        ai["severity"] = "P1"
        ai["confidence"] = max(float(ai.get("confidence", 0.75)), 0.9)
        ai["reasoning"] = "Datadog P1 override: critical monitoring alert triggered."

    is_dup, dup_id, sim = detect_duplicate(db, title, description, threshold=0.85)

    ticket = Ticket(
        title=title,
        description=description,
        reporter="Datadog Monitor",
        department="Infrastructure",
        severity=ai["severity"],
        confidence=float(ai["confidence"]),
        assigned_team=ai["assigned_team"],
        suggested_fixes=ai["suggested_fixes"],
        is_duplicate=bool(is_dup),
        duplicate_ticket_id=dup_id,
        similarity_score=float(sim),
        escalated=False,
        jira_issue_key=None,
        lifecycle_status="TRIAGED",
        source="datadog",
        alert_metadata=metadata,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    if ticket.severity == "P1" and not ticket.is_duplicate:
        ticket = escalate_if_needed(db, ticket)

    decision_trace = _build_decision_trace(
        title=ticket.title,
        description=ticket.description,
        assigned_team=ticket.assigned_team,
        severity=ticket.severity,
        similarity_score=ticket.similarity_score,
        escalated=ticket.escalated,
        triage_source=str(ai.get("triage_source", "")) or None,
    )

    return _to_out(ticket, ai_reasoning=str(ai.get("reasoning", "")), decision_trace=decision_trace)


@app.patch("/tickets/{ticket_id}/status", response_model=TicketOut)
def update_ticket_status(ticket_id: int, payload: TicketStatusUpdate, db: Session = Depends(get_db)) -> TicketOut:
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")

    status = payload.lifecycle_status.strip().upper()
    allowed = {"RECEIVED", "TRIAGED", "ESCALATED", "RESOLVED"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid lifecycle_status. Allowed: {sorted(allowed)}")

    t.lifecycle_status = status
    db.add(t)
    db.commit()
    db.refresh(t)
    return _to_out(t)


@app.get("/dashboard/metrics", response_model=DashboardMetrics)
def dashboard_metrics(db: Session = Depends(get_db)) -> DashboardMetrics:
    tickets = db.query(Ticket).all()

    total = len(tickets)
    escalated = sum(1 for t in tickets if t.escalated)
    duplicates = sum(1 for t in tickets if t.is_duplicate)
    monitoring = sum(1 for t in tickets if getattr(t, "source", "manual") == "datadog")

    severity_counts = Counter([t.severity for t in tickets])
    team_counts = Counter([t.assigned_team for t in tickets])

    by_severity = [{"name": k, "value": int(v)} for k, v in sorted(severity_counts.items())]
    by_team = [{"name": k, "value": int(v)} for k, v in sorted(team_counts.items())]

    prevented = duplicates
    hours_per_duplicate = float(os.getenv("HOURS_SAVED_PER_DUPLICATE", "1.5"))
    hours_saved = round(prevented * hours_per_duplicate, 2)

    return DashboardMetrics(
        total_tickets=total,
        escalated_tickets=escalated,
        duplicate_tickets=duplicates,
        monitoring_tickets=monitoring,
        duplicate_tickets_prevented=prevented,
        estimated_engineer_hours_saved=hours_saved,
        by_severity=by_severity,
        by_team=by_team,
    )


@app.post("/seed", response_model=SeedResponse)
def seed(db: Session = Depends(get_db)) -> SeedResponse:
    inserted = seed_demo_tickets(db)
    return SeedResponse(inserted=inserted)


# ---------------------------------------------------------------------------
# V2: Webhook endpoint for n8n / Jira closure sync
# ---------------------------------------------------------------------------
@app.post("/webhook/jira-closure")
def jira_closure_webhook(
    payload: JiraClosureWebhook,
    db: Session = Depends(get_db),
) -> dict:
    """Receive Jira issue closure events forwarded by n8n.

    Updates the local ticket status and resolved_at timestamp.
    """
    ticket = (
        db.query(Ticket)
        .filter(Ticket.jira_issue_key == payload.jira_issue_key)
        .first()
    )
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail=f"No ticket found with jira_issue_key={payload.jira_issue_key}",
        )

    from datetime import datetime, timezone

    ticket.status = payload.status
    ticket.lifecycle_status = "RESOLVED" if payload.status in ("resolved", "closed") else ticket.lifecycle_status
    ticket.resolved_at = datetime.now(timezone.utc)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {
        "ok": True,
        "ticket_id": ticket.id,
        "status": ticket.status,
        "resolved_at": str(ticket.resolved_at),
        "resolved_by": payload.resolved_by,
    }
