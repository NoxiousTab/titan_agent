from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    reporter: str = Field(..., min_length=2, max_length=120)
    department: str = Field(..., min_length=2, max_length=120)


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    reporter: str
    department: str

    severity: str
    confidence: float
    assigned_team: str
    suggested_fixes: Any

    is_duplicate: bool
    duplicate_ticket_id: Optional[int] = None
    similarity_score: float

    escalated: bool
    jira_issue_key: Optional[str] = None
    created_at: datetime

    ai_reasoning: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    total_tickets: int
    escalated_tickets: int
    duplicate_tickets: int
    by_severity: list[dict]
    by_team: list[dict]


class SeedResponse(BaseModel):
    inserted: int
