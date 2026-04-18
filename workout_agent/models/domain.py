"""Domain models shared across agents and API boundaries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserMetrics(BaseModel):
    """Physical metrics used for plan personalization."""

    age: int = Field(ge=13, le=100)
    height_cm: float = Field(ge=100, le=250)
    weight_kg: float = Field(ge=30, le=350)
    sex: Literal["female", "male", "other", "prefer_not_to_say"] = "prefer_not_to_say"

    model_config = ConfigDict(extra="forbid")


class TrainingAvailability(BaseModel):
    """Weekly availability constraints."""

    days_per_week: int = Field(ge=1, le=7)
    minutes_per_session: int = Field(ge=20, le=180)
    preferred_days: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class UserProfile(BaseModel):
    """Collected user information from the intake flow."""

    user_id: str | None = None
    goals: list[str] = Field(min_length=1)
    metrics: UserMetrics
    availability: TrainingAvailability
    equipment: list[str] = Field(default_factory=list)
    experience_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class ConstraintProfile(BaseModel):
    """Injuries, chronic conditions, and hard restrictions."""

    injuries: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class Exercise(BaseModel):
    """Exercise document retrieved from the knowledge base."""

    exercise_id: str
    name: str
    primary_muscles: list[str] = Field(default_factory=list)
    secondary_muscles: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    difficulty: str | None = None
    instructions: str | None = None
    category: str | None = None
    score: float | None = None

    model_config = ConfigDict(extra="ignore")


class ExercisePrescription(BaseModel):
    """Scheduled prescription of one exercise."""

    exercise_id: str
    exercise_name: str
    sets: int = Field(ge=1, le=10)
    reps: str
    rest_seconds: int = Field(ge=30, le=300)
    target_rpe: float | None = Field(default=None, ge=1.0, le=10.0)
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class DayPlan(BaseModel):
    """Single training day plan."""

    day_name: str
    focus: str
    recovery_hours_after_day: int = Field(ge=12, le=96)
    exercises: list[ExercisePrescription] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class WeekPlan(BaseModel):
    """Week-level schedule container."""

    week_number: int = Field(ge=1)
    days: list[DayPlan] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ProgressionTarget(BaseModel):
    """Progression intent for a given week."""

    week_number: int = Field(ge=1)
    volume_multiplier: float = Field(gt=0.0, le=2.0)
    intensity_delta_pct: float = Field(ge=-50.0, le=100.0)
    load_adjustment_kg: float | None = None
    rep_adjustment: int | None = None
    target_rpe: float | None = Field(default=None, ge=1.0, le=10.0)
    deload: bool = False
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class SafetyIssue(BaseModel):
    """A safety issue detected in the candidate plan."""

    exercise_name: str
    reason: str
    severity: Literal["low", "moderate", "high", "critical"] = "moderate"
    recommendation: str | None = None

    model_config = ConfigDict(extra="forbid")


class SafetyAssessment(BaseModel):
    """Safety outcome returned by risk_assessment."""

    has_critical_issues: bool = False
    issues: list[SafetyIssue] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class DecisionExplanation(BaseModel):
    """Human-readable explanation for one decision."""

    decision_id: str
    title: str
    rationale: str
    supporting_factors: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class AgentError(BaseModel):
    """Structured error representation collected in state.errors."""

    agent: str
    message: str
    details: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid")


class WorkoutPlan(BaseModel):
    """Final exported workout plan."""

    plan_id: str
    request_id: str
    user_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    weeks: int = Field(ge=1, le=52)
    weekly_schedule: list[WeekPlan] = Field(default_factory=list)
    progression_targets: list[ProgressionTarget] = Field(default_factory=list)
    safety_assessment: SafetyAssessment = Field(default_factory=SafetyAssessment)
    explanations: list[DecisionExplanation] = Field(default_factory=list)
    status: Literal["approved", "needs_review", "failed"] = "approved"
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")
