from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    reporter: Optional[str] = None
    department: Optional[str] = None


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    reporter: str
    department: str

    source: str
    metadata: Optional[Any] = None

    severity: str
    confidence: float
    assigned_team: str
    suggested_fixes: Any

    is_duplicate: bool
    duplicate_ticket_id: Optional[int] = None
    similarity_score: float

    escalated: bool
    jira_issue_key: Optional[str] = None
    lifecycle_status: str
    created_at: datetime

    ai_reasoning: Optional[str] = None
    decision_trace: Optional[Any] = None

    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    total_tickets: int
    escalated_tickets: int
    duplicate_tickets: int
    monitoring_tickets: int
    duplicate_tickets_prevented: int
    estimated_engineer_hours_saved: float
    by_severity: list[dict]
    by_team: list[dict]


class SeedResponse(BaseModel):
    inserted: int


class TicketStatusUpdate(BaseModel):
    lifecycle_status: str = Field(..., min_length=3, max_length=20)
