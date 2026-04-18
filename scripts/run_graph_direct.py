"""Run the LangGraph workflow directly without HTTP."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workout_agent.core.state import AgentState, build_initial_state
from workout_agent.models.api import GeneratePlanRequest
from workout_agent.models.domain import (
    ConstraintProfile,
    TrainingAvailability,
    UserMetrics,
    UserProfile,
)
from workout_agent.services.runtime import AppRuntime


TEST_PROFILE: dict[str, Any] = {
    "user_id": "test-001",
    "goals": "build muscle, lose fat",
    "age": 25,
    "weight_kg": 80,
    "height_cm": 180,
    "fitness_level": "intermediate",
    "training_days_per_week": 4,
    "session_duration_minutes": 60,
    "available_equipment": ["barbell", "dumbbells", "rack"],
    "injuries": ["left_knee_pain"],
    "conditions": [],
    "restrictions": [],
}


def _parse_goals(goals: str) -> list[str]:
    return [goal.strip() for goal in goals.split(",") if goal.strip()]


def _build_request_from_test_profile() -> GeneratePlanRequest:
    profile = UserProfile(
        user_id=TEST_PROFILE["user_id"],
        goals=_parse_goals(TEST_PROFILE["goals"]),
        metrics=UserMetrics(
            age=TEST_PROFILE["age"],
            weight_kg=float(TEST_PROFILE["weight_kg"]),
            height_cm=float(TEST_PROFILE["height_cm"]),
        ),
        availability=TrainingAvailability(
            days_per_week=int(TEST_PROFILE["training_days_per_week"]),
            minutes_per_session=int(TEST_PROFILE["session_duration_minutes"]),
            preferred_days=[],
        ),
        equipment=list(TEST_PROFILE["available_equipment"]),
        experience_level=TEST_PROFILE["fitness_level"],
    )

    constraints = ConstraintProfile(
        injuries=list(TEST_PROFILE["injuries"]),
        chronic_conditions=list(TEST_PROFILE["conditions"]),
        restrictions=list(TEST_PROFILE["restrictions"]),
        contraindications=[],
    )

    return GeneratePlanRequest(
        user_profile=profile,
        constraints=constraints,
        weeks=4,
        use_eval_model=False,
    )


def _len_or_zero(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (list, dict, set, tuple, str)):
        return len(value)
    return 0


def _error_signature(error: Any) -> str:
    if hasattr(error, "agent") and hasattr(error, "message"):
        return f"{error.agent}: {error.message}"
    if isinstance(error, dict):
        return f"{error.get('agent', 'unknown')}: {error.get('message', 'unknown error')}"
    return str(error)


def _state_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    safety = state.get("safety_assessment")
    final_plan = state.get("final_plan")
    errors = state.get("errors", [])

    return {
        "plan_context_keys": set((state.get("plan_context") or {}).keys()),
        "candidate_exercises": _len_or_zero(state.get("candidate_exercises")),
        "weekly_schedule": _len_or_zero(state.get("weekly_schedule")),
        "progression_targets": _len_or_zero(state.get("progression_targets")),
        "safety_issue_count": _len_or_zero(getattr(safety, "issues", None))
        if safety is not None
        else 0,
        "explanations": _len_or_zero(state.get("explanations")),
        "final_plan_id": getattr(final_plan, "plan_id", None) if final_plan is not None else None,
        "errors": [_error_signature(error) for error in errors],
        "risk_retry_count": state.get("risk_retry_count"),
        "should_reselect_exercises": state.get("should_reselect_exercises"),
    }


def _describe_state_additions(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    changes: list[str] = []

    added_context_keys = sorted(after["plan_context_keys"] - before["plan_context_keys"])
    if added_context_keys:
        changes.append(f"plan_context keys added: {', '.join(added_context_keys)}")

    before_candidates = before["candidate_exercises"]
    after_candidates = after["candidate_exercises"]
    if after_candidates > before_candidates:
        changes.append(f"candidate_exercises: {after_candidates}")

    before_weeks = before["weekly_schedule"]
    after_weeks = after["weekly_schedule"]
    if after_weeks > before_weeks:
        changes.append(f"weekly_schedule weeks: {after_weeks}")

    before_progress = before["progression_targets"]
    after_progress = after["progression_targets"]
    if after_progress > before_progress:
        changes.append(f"progression_targets: {after_progress}")

    if after["safety_issue_count"] > before["safety_issue_count"]:
        changes.append(f"safety_assessment issues: {after['safety_issue_count']}")

    before_explanations = before["explanations"]
    after_explanations = after["explanations"]
    if after_explanations > before_explanations:
        changes.append(f"explanations: {after_explanations}")

    if before["final_plan_id"] is None and after["final_plan_id"] is not None:
        changes.append(f"final_plan created: {after['final_plan_id']}")

    before_errors = before["errors"]
    after_errors = after["errors"]
    if len(after_errors) > len(before_errors):
        new_errors = after_errors[len(before_errors) :]
        for error_signature in new_errors:
            changes.append(f"error added: {error_signature}")

    if before["risk_retry_count"] != after["risk_retry_count"]:
        changes.append(f"risk_retry_count: {after['risk_retry_count']}")

    if before["should_reselect_exercises"] != after["should_reselect_exercises"]:
        changes.append(f"should_reselect_exercises: {after['should_reselect_exercises']}")

    return changes


def _merge_state(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in update.items():
        merged[key] = value
    return merged


async def run_graph() -> None:
    runtime = AppRuntime()
    await runtime.startup()

    try:
        request = _build_request_from_test_profile()
        initial_state: AgentState = build_initial_state(
            request,
            runtime=runtime.runtime_dependencies,
        )

        print(f"Running graph directly for request_id={initial_state['request_id']}")

        current_state: dict[str, Any] = dict(initial_state)
        async for event in runtime.graph.astream(initial_state, stream_mode="updates"):
            if not isinstance(event, dict):
                continue

            for agent_name, update in event.items():
                if not isinstance(update, dict):
                    continue

                before = _state_snapshot(current_state)
                current_state = _merge_state(current_state, update)
                after = _state_snapshot(current_state)
                added = _describe_state_additions(before, after)

                print(f"\n[{agent_name}]")
                if added:
                    for item in added:
                        print(f"- {item}")
                else:
                    print("- no tracked additions")

        print("\nFINAL PLAN")
        final_plan = current_state.get("final_plan")
        if final_plan is None:
            print("null")
        elif hasattr(final_plan, "model_dump"):
            print(json.dumps(final_plan.model_dump(mode="python"), indent=2, default=str))
        else:
            print(json.dumps(final_plan, indent=2, default=str))

        errors = current_state.get("errors", [])
        print("\nSTATE ERRORS")
        if not errors:
            print("- none")
        else:
            for error in errors:
                if hasattr(error, "model_dump"):
                    payload = error.model_dump(mode="python")
                elif isinstance(error, dict):
                    payload = error
                else:
                    payload = {"message": str(error)}

                agent = payload.get("agent", "unknown")
                message = payload.get("message", "unknown error")
                details = payload.get("details")
                print(f"- {agent}: {message}")
                if details:
                    print(f"  details: {details}")
    finally:
        await runtime.shutdown()


if __name__ == "__main__":
    asyncio.run(run_graph())
