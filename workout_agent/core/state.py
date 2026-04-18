"""Shared LangGraph state definitions and helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypedDict
from uuid import uuid4

from workout_agent.models.api import GeneratePlanRequest
from workout_agent.models.domain import (
    AgentError,
    ConstraintProfile,
    DecisionExplanation,
    Exercise,
    ProgressionTarget,
    SafetyAssessment,
    UserProfile,
    WeekPlan,
    WorkoutPlan,
)


class RuntimeDependencies(TypedDict):
    """Runtime services injected into the agent graph."""

    settings: Any
    ollama_client: Any
    exercise_repository: Any
    workout_plan_repository: Any
    user_repository: Any
    session_log_repository: Any


class AgentState(TypedDict):
    """Shared mutable state for all pipeline agents."""

    request_id: str
    requested_weeks: int
    use_eval_model: bool

    user_profile: UserProfile | None
    constraints: ConstraintProfile | None

    plan_context: dict[str, Any]
    candidate_exercises: list[Exercise]
    weekly_schedule: list[WeekPlan]
    progression_targets: list[ProgressionTarget]
    safety_assessment: SafetyAssessment | None
    explanations: list[DecisionExplanation]
    final_plan: WorkoutPlan | None

    should_reselect_exercises: bool
    risk_exhausted: bool
    risk_retry_count: int
    max_risk_retries: int
    blocked_exercise_ids: list[str]

    errors: list[AgentError]
    runtime: RuntimeDependencies


def append_error(state: AgentState, agent: str, message: str, details: str | None = None) -> None:
    """Append a structured error to state.errors."""

    state["errors"].append(AgentError(agent=agent, message=message, details=details))


def build_initial_state(request: GeneratePlanRequest, runtime: RuntimeDependencies) -> AgentState:
    """Create a fresh state object for each generation request."""

    settings = runtime["settings"]
    return AgentState(
        request_id=str(uuid4()),
        requested_weeks=request.weeks,
        use_eval_model=request.use_eval_model,
        user_profile=request.user_profile,
        constraints=request.constraints,
        plan_context={},
        candidate_exercises=[],
        weekly_schedule=[],
        progression_targets=[],
        safety_assessment=None,
        explanations=[],
        final_plan=None,
        should_reselect_exercises=False,
        risk_exhausted=False,
        risk_retry_count=0,
        max_risk_retries=settings.max_risk_retries,
        blocked_exercise_ids=[],
        errors=[],
        runtime=runtime,
    )


def clone_state(state: AgentState) -> AgentState:
    """Clone state for defensive updates when needed."""

    return deepcopy(state)
