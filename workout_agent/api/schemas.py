"""Shared API schemas and response wrappers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from workout_agent.models.domain import EvidenceSource, MedicalConstraint

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper for all endpoints."""

    success: bool
    data: T | None = None
    error: str | None = None
    request_id: str

    model_config = ConfigDict(extra="forbid")


class UserPlanSummary(BaseModel):
    """Lightweight plan summary for user listing endpoint."""

    plan_id: str
    status: str
    created_at: datetime
    week_number: int = Field(ge=1)

    model_config = ConfigDict(extra="forbid")


class PlanFeedbackRequest(BaseModel):
    """Feedback payload submitted after a training session."""

    session_number: int = Field(ge=1)
    completed: bool
    perceived_difficulty: int = Field(ge=1, le=5)
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class PlanFeedbackResponse(BaseModel):
    """Response payload with created feedback log identifier."""

    log_id: str

    model_config = ConfigDict(extra="forbid")


class HealthResponse(BaseModel):
    """Health endpoint data payload."""

    status: str
    mongodb: str

    model_config = ConfigDict(extra="forbid")


class SessionEvent(BaseModel):
    """One persisted orchestration event for frontend progress polling."""

    request_id: str
    agent: str
    event: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    model_config = ConfigDict(extra="forbid")


class ConstraintCatalogItem(BaseModel):
    """Read-only medical constraint catalog item."""

    condition_id: str
    canonical_name: str
    condition_type: str
    risk_level: str
    evidence_level: str | None = None
    affected_body_parts: list[str] = Field(default_factory=list)
    movement_restrictions: list[str] = Field(default_factory=list)
    safe_alternatives: list[str] = Field(default_factory=list)
    sources: list[EvidenceSource] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ConstraintSearchResponse(BaseModel):
    """Search result payload with full constraint records."""

    items: list[MedicalConstraint] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
