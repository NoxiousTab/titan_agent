from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reporter: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)

    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="P4")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    assigned_team: Mapped[str] = mapped_column(String(120), nullable=False, default="Application Support")

    suggested_fixes: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)

    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duplicate_ticket_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    jira_issue_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    lifecycle_status: Mapped[str] = mapped_column(String(20), nullable=False, default="RECEIVED")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
