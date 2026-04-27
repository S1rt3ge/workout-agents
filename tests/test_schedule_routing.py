from workout_agent.agents.schedule_maker import categorize_exercise, enforce_day_routing
from workout_agent.models.domain import Exercise


def exercise(name: str) -> Exercise:
    return Exercise(
        exercise_id=name.lower().replace(" ", "_"),
        name=name,
        category="strength",
    )


def names(exercises: list[Exercise]) -> list[str]:
    return [item.name for item in exercises]


def test_rear_delt_routes_to_pull_before_generic_fly() -> None:
    assert categorize_exercise("Rear Delt Fly") == "pull"


def test_leg_curl_routes_to_lower_before_generic_curl() -> None:
    assert categorize_exercise("Leg Curl Machine") == "lower"


def test_push_day_prioritizes_triceps_and_excludes_rear_delt() -> None:
    candidates = [
        exercise("Dumbbell Bench Press"),
        exercise("Incline Dumbbell Press"),
        exercise("Machine Chest Press"),
        exercise("Rear Delt Fly"),
        exercise("Cable Tricep Pushdown"),
    ]

    routed_names = names(
        enforce_day_routing(
            "Push",
            candidates,
            candidates,
            shoulder_sensitive=True,
        )
    )

    assert "Rear Delt Fly" not in routed_names
    assert "Cable Tricep Pushdown" in routed_names
    assert sum("Press" in name or "Bench" in name for name in routed_names) <= 2


def test_pull_day_keeps_rear_delt_and_excludes_leg_curl() -> None:
    candidates = [
        exercise("Rear Delt Fly"),
        exercise("Leg Curl Machine"),
        exercise("Lat Pulldown"),
        exercise("Seated Cable Row"),
    ]

    routed_names = names(enforce_day_routing("Pull", candidates, candidates))

    assert "Rear Delt Fly" in routed_names
    assert "Leg Curl Machine" not in routed_names


def test_pressure_sensitive_lower_day_removes_heavy_squat_and_deadlift() -> None:
    candidates = [
        exercise("Barbell Back Squat"),
        exercise("Romanian Deadlift"),
        exercise("Dumbbell Romanian Deadlift"),
        exercise("Goblet Squat"),
        exercise("Leg Press"),
        exercise("Step-Up"),
        exercise("Hip Thrust"),
        exercise("Glute Bridge"),
        exercise("Leg Curl Machine"),
        exercise("Calf Raise"),
    ]

    routed_names = names(
        enforce_day_routing(
            "Lower Body",
            candidates,
            candidates,
            pressure_sensitive=True,
        )
    )

    assert "Barbell Back Squat" not in routed_names
    assert not any("Deadlift" in name for name in routed_names)
    assert "Leg Press" in routed_names
    assert "Hip Thrust" in routed_names
