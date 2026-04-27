"""API request/response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from workout_agent.models.domain import AgentError, ConstraintProfile, UserProfile, WorkoutPlan


class GeneratePlanRequest(BaseModel):
    """Payload for workout plan generation."""

    request_id: str | None = None
    user_profile: UserProfile
    constraints: ConstraintProfile
    weeks: int = Field(default=4, ge=1, le=24)
    use_eval_model: bool = Field(default=False)

    model_config = ConfigDict(extra="forbid")


class GeneratePlanResponse(BaseModel):
    """Structured generation response."""

    request_id: str
    status: str
    plan: WorkoutPlan | None = None
    errors: list[AgentError] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
