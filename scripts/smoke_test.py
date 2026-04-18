"""Smoke test for importability and AgentState schema shape."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workout_agent.core.state import AgentState, RuntimeDependencies, build_initial_state
from workout_agent.models.api import GeneratePlanRequest
from workout_agent.models.domain import (
    ConstraintProfile,
    TrainingAvailability,
    UserMetrics,
    UserProfile,
)


def assert_imports() -> None:
    """Import all required modules and validate model symbols are present."""

    modules = [
        "workout_agent.agents.information_receiver",
        "workout_agent.agents.constraint_receiver",
        "workout_agent.agents.exercise_selector",
        "workout_agent.agents.schedule_maker",
        "workout_agent.agents.progress_planner",
        "workout_agent.agents.risk_assessment",
        "workout_agent.agents.explainability",
        "workout_agent.agents.plan_export",
        "workout_agent.services.workout_graph",
        "workout_agent.core.config",
        "workout_agent.models.domain",
        "workout_agent.models.api",
    ]

    for module_name in modules:
        importlib.import_module(module_name)

    from workout_agent.models import api as api_models
    from workout_agent.models import domain as domain_models

    domain_model_names = [
        "UserMetrics",
        "TrainingAvailability",
        "UserProfile",
        "ConstraintProfile",
        "Exercise",
        "ExercisePrescription",
        "DayPlan",
        "WeekPlan",
        "ProgressionTarget",
        "SafetyIssue",
        "SafetyAssessment",
        "DecisionExplanation",
        "AgentError",
        "WorkoutPlan",
    ]
    api_model_names = ["GeneratePlanRequest", "GeneratePlanResponse"]

    for model_name in [*domain_model_names, *api_model_names]:
        source_module = domain_models if model_name in domain_model_names else api_models
        model = getattr(source_module, model_name)
        if not isinstance(model, type) or not issubclass(model, BaseModel):
            raise TypeError(f"{model_name} is not a Pydantic model")


class _DummySettings:
    max_risk_retries = 2


def assert_state_schema() -> None:
    """Build minimal state object and verify required keys exist."""

    request = GeneratePlanRequest(
        user_profile=UserProfile(
            user_id="smoke-user",
            goals=["build strength"],
            metrics=UserMetrics(age=30, height_cm=175.0, weight_kg=75.0),
            availability=TrainingAvailability(days_per_week=3, minutes_per_session=45),
            equipment=["bodyweight"],
            experience_level="beginner",
        ),
        constraints=ConstraintProfile(),
        weeks=2,
        use_eval_model=False,
    )

    runtime: RuntimeDependencies = {
        "settings": _DummySettings(),
        "ollama_client": object(),
        "exercise_repository": object(),
        "workout_plan_repository": object(),
        "user_repository": object(),
        "session_log_repository": object(),
    }

    state = build_initial_state(request, runtime)

    required_state_keys = set(getattr(AgentState, "__required_keys__", set()))
    required_runtime_keys = set(getattr(RuntimeDependencies, "__required_keys__", set()))

    missing_state = required_state_keys.difference(state.keys())
    missing_runtime = required_runtime_keys.difference(state["runtime"].keys())

    if missing_state:
        raise KeyError(f"Missing AgentState keys: {sorted(missing_state)}")
    if missing_runtime:
        raise KeyError(f"Missing runtime dependency keys: {sorted(missing_runtime)}")


def main() -> None:
    assert_imports()
    print("ALL IMPORTS OK")
    assert_state_schema()
    print("STATE SCHEMA OK")


if __name__ == "__main__":
    main()
