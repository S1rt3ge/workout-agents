"""Verification script for retrieval-first medical constraint flow."""

# ruff: noqa: E402

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workout_agent.models.api import GeneratePlanRequest
from workout_agent.models.domain import (
    ConstraintProfile,
    TrainingAvailability,
    UserMetrics,
    UserProfile,
)
from workout_agent.services.runtime import AppRuntime


def _build_request() -> GeneratePlanRequest:
    return GeneratePlanRequest(
        user_profile=UserProfile(
            user_id="constraints-flow-test",
            goals=["build muscle", "maintain conditioning"],
            metrics=UserMetrics(
                age=29,
                height_cm=178.0,
                weight_kg=80.0,
            ),
            availability=TrainingAvailability(
                days_per_week=4,
                minutes_per_session=55,
                preferred_days=[],
            ),
            equipment=["dumbbells", "bench", "bodyweight", "cable_machine"],
            experience_level="intermediate",
            notes="Need a safe plan around shoulder pain.",
        ),
        constraints=ConstraintProfile(
            injuries=["shoulder strain"],
            chronic_conditions=[],
            restrictions=[],
            contraindications=[],
        ),
        weeks=4,
        use_eval_model=False,
    )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _collect_exercise_names(plan_payload: dict) -> list[str]:
    names: list[str] = []
    for week in plan_payload.get("weekly_schedule", []):
        for day in week.get("days", []):
            for exercise in day.get("exercises", []):
                name = exercise.get("exercise_name")
                if name:
                    names.append(str(name))
    return names


async def main() -> None:
    runtime = AppRuntime()
    await runtime.startup()

    try:
        matches = await runtime.medical_constraint_repository.find_by_aliases_or_names(
            ["shoulder strain"]
        )
        _assert(bool(matches), "medical_constraints lookup failed for shoulder strain")

        result = await runtime.workout_planner_service.generate_plan(_build_request())
        _assert(result.plan is not None, "plan generation returned no plan")

        plan = result.plan.model_dump(mode="python")
        constraint_summary = plan.get("constraint_summary", [])
        _assert(bool(constraint_summary), "constraint_summary is empty")
        _assert(
            any(
                item.get("condition_id") == "shoulder_pain_overhead_restriction"
                for item in constraint_summary
            ),
            "shoulder strain input was not resolved into the expected shoulder safety cluster",
        )

        exercise_names = [name.lower() for name in _collect_exercise_names(plan)]
        banned_keywords = ["overhead press", "arnold press", "lateral raise"]
        for keyword in banned_keywords:
            _assert(
                not any(keyword in name for name in exercise_names),
                f"unsafe exercise containing '{keyword}' was present in final plan",
            )

        explanations = plan.get("explanations", [])
        joined_explanations = " ".join(
            str(item.get("rationale", "")) for item in explanations
        ).lower()
        _assert(
            "shoulder pain with overhead loading restriction" in joined_explanations
            or "resolved shoulder strain profile" in joined_explanations
            or "movement restriction profile retrieved" in joined_explanations
            or "shoulder strain" in joined_explanations,
            "explainability output does not reference safety reasoning from resolved constraints",
        )

        evidence_references = plan.get("evidence_references", [])
        _assert(bool(evidence_references), "evidence_references is empty")

        print("PASS: matching condition found in medical_constraints")
        print("PASS: resolved constraint propagated to final plan")
        print("PASS: unsafe shoulder-loading exercises excluded")
        print("PASS: explainability references retrieved safety reasoning")
        print("PASS: evidence references included in output")
    finally:
        await runtime.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
