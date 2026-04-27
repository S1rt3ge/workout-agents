"""Agent 5: generate week-over-week progression targets."""

from __future__ import annotations

from pydantic import BaseModel, Field

from workout_agent.agents.common import call_structured_llm, log_agent_event
from workout_agent.agents.prompts import PROGRESS_PLANNER_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import ProgressionTarget


class ProgressPlannerOutput(BaseModel):
    """Structured progression response from LLM."""

    targets: list[ProgressionTarget] = Field(default_factory=list)


def _collect_schedule_exercises(state: AgentState) -> dict[str, list[str]]:
    grouped = {"pressing": [], "compound": [], "all": []}
    seen: set[str] = set()

    for week in state["weekly_schedule"][:1]:
        for day in week.days:
            for exercise in day.exercises:
                name = exercise.exercise_name
                if name not in seen:
                    grouped["all"].append(name)
                    seen.add(name)

                name_lower = name.lower()
                if any(keyword in name_lower for keyword in ("press", "bench", "incline", "dip")):
                    if name not in grouped["pressing"]:
                        grouped["pressing"].append(name)
                if any(
                    keyword in name_lower
                    for keyword in (
                        "squat",
                        "deadlift",
                        "row",
                        "pulldown",
                        "pull-up",
                        "pullup",
                        "press",
                        "lunge",
                        "leg press",
                        "hip thrust",
                    )
                ):
                    if name not in grouped["compound"]:
                        grouped["compound"].append(name)

    return grouped


def _build_specific_note(week: int, grouped_names: dict[str, list[str]]) -> str:
    pressing = grouped_names["pressing"]
    compounds = grouped_names["compound"]
    pressing_label = ", ".join(pressing[:3]) if pressing else "pressing movements"
    compound_label = ", ".join(compounds[:4]) if compounds else "compound lifts"

    if week == 1:
        return (
            "Week 1: establish baseline sets x reps x weight for each exercise and "
            "stop with 2-3 reps in reserve."
        )
    if week == 2:
        return (
            f"Week 2: add 2.5kg to {pressing_label} or add 1 rep per set if "
            "load jumps are too large."
        )
    if week == 3:
        return f"Week 3: add 1 set to {compound_label} or add 5kg where technique stays controlled."
    return (
        "Week 4: deload - reduce volume 40%, maintain load, and keep all sets "
        "comfortably away from failure."
    )


def _normalize_progression_target(
    target: ProgressionTarget,
    grouped_names: dict[str, list[str]],
) -> ProgressionTarget:
    week = target.week_number
    if week == 1:
        return target.model_copy(
            update={
                "volume_multiplier": 1.0,
                "intensity_delta_pct": 0.0,
                "load_adjustment_kg": 0.0,
                "rep_adjustment": 0,
                "target_rpe": 7.0,
                "deload": False,
                "notes": _build_specific_note(week, grouped_names),
            }
        )
    if week == 2:
        return target.model_copy(
            update={
                "volume_multiplier": 1.0,
                "intensity_delta_pct": 5.0,
                "load_adjustment_kg": 2.5,
                "rep_adjustment": 1,
                "target_rpe": 7.5,
                "deload": False,
                "notes": _build_specific_note(week, grouped_names),
            }
        )
    if week == 3:
        return target.model_copy(
            update={
                "volume_multiplier": 1.2,
                "intensity_delta_pct": 10.0,
                "load_adjustment_kg": 5.0,
                "rep_adjustment": 0,
                "target_rpe": 8.0,
                "deload": False,
                "notes": _build_specific_note(week, grouped_names),
            }
        )
    return target.model_copy(
        update={
            "volume_multiplier": 0.6,
            "intensity_delta_pct": 5.0,
            "load_adjustment_kg": 0.0,
            "rep_adjustment": 0,
            "target_rpe": 6.0,
            "deload": True,
            "notes": _build_specific_note(week, grouped_names),
        }
    )


def _default_progression(weeks: int) -> list[ProgressionTarget]:
    targets: list[ProgressionTarget] = []
    for week in range(1, weeks + 1):
        deload = week % 4 == 0
        if week == 1:
            volume_multiplier = 1.0
            intensity_delta_pct = 0.0
            load_adjustment_kg = 0.0
            rep_adjustment = 0
            target_rpe = 7.0
        elif week == 2:
            volume_multiplier = 1.0
            intensity_delta_pct = 5.0
            load_adjustment_kg = 2.5
            rep_adjustment = 1
            target_rpe = 7.5
        elif week == 3:
            volume_multiplier = 1.2
            intensity_delta_pct = 10.0
            load_adjustment_kg = 5.0
            rep_adjustment = 0
            target_rpe = 8.0
        else:
            volume_multiplier = 0.6
            intensity_delta_pct = 0.0
            load_adjustment_kg = 0.0
            rep_adjustment = 0
            target_rpe = 6.0
        targets.append(
            ProgressionTarget(
                week_number=week,
                volume_multiplier=volume_multiplier,
                intensity_delta_pct=intensity_delta_pct,
                load_adjustment_kg=load_adjustment_kg,
                rep_adjustment=rep_adjustment,
                target_rpe=target_rpe,
                deload=deload,
                notes="Week-by-week progression",
            )
        )
    return targets


async def run(state: AgentState) -> AgentState:
    """Derive progression curve for scheduled plan."""

    agent = "progress_planner"
    await log_agent_event(state, agent=agent, event="started")

    profile = state["user_profile"]
    if profile is None:
        append_error(state, agent=agent, message="User profile is missing")
        return state

    output = await call_structured_llm(
        state,
        agent=agent,
        system_prompt=PROGRESS_PLANNER_PROMPT,
        payload={
            "weeks": state["requested_weeks"],
            "experience_level": profile.experience_level,
            "schedule_summary": [
                {
                    "week_number": week.week_number,
                    "days": [{"day_name": day.day_name, "focus": day.focus} for day in week.days],
                }
                for week in state["weekly_schedule"]
            ],
        },
        output_model=ProgressPlannerOutput,
        record_error_on_failure=False,
    )

    targets = (
        output.targets
        if output and output.targets
        else _default_progression(state["requested_weeks"])
    )
    targets = sorted(targets, key=lambda item: item.week_number)

    grouped_names = _collect_schedule_exercises(state)
    normalized_targets: list[ProgressionTarget] = []
    for target in targets:
        normalized_targets.append(_normalize_progression_target(target, grouped_names))
    targets = normalized_targets

    if not targets:
        append_error(state, agent=agent, message="No progression targets generated")
        return state

    state["progression_targets"] = targets
    await log_agent_event(
        state, agent=agent, event="completed", payload={"target_count": len(targets)}
    )
    return state
