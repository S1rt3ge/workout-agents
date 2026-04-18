"""Shared API schemas and response wrappers."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

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
