"""Agent 4: distribute selected exercises into weekly day plans."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from workout_agent.agents.common import call_structured_llm, log_agent_event
from workout_agent.agents.prompts import SCHEDULE_MAKER_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import Exercise
from workout_agent.models.domain import DayPlan, ExercisePrescription, WeekPlan

MOVEMENT_CATEGORIES = {
    "push": [
        "bench press",
        "chest press",
        "chest fly",
        "push-up",
        "pushup",
        "overhead press",
        "shoulder press",
        "arnold press",
        "lateral raise",
        "front raise",
        "tricep",
        "skull crusher",
        "dip",
        "cable crossover",
        "incline press",
        "decline press",
        "flye",
        "fly",
    ],
    "pull": [
        "row",
        "pull-up",
        "pullup",
        "chin-up",
        "chinup",
        "lat pulldown",
        "face pull",
        "shrug",
        "curl",
        "straight arm",
        "pullover",
        "rear delt",
        "rear_delt",
        "t-bar",
        "cable pull",
    ],
    "lower": [
        "squat",
        "deadlift",
        "lunge",
        "leg press",
        "leg curl",
        "leg extension",
        "hip thrust",
        "glute bridge",
        "calf raise",
        "step-up",
        "split squat",
        "bulgarian",
        "hack squat",
        "sumo",
        "rdl",
        "good morning",
    ],
    "core": [
        "plank",
        "crunch",
        "sit-up",
        "ab wheel",
        "rollout",
        "dead bug",
        "pallof",
        "russian twist",
        "hanging leg",
        "cable crunch",
        "farmer carry",
    ],
    "cardio": [
        "jump rope",
        "box jump",
        "battle rope",
        "sled",
        "assault bike",
        "row machine",
        "kettlebell swing",
        "burpee",
    ],
}


class DayTemplate(BaseModel):
    """Day template returned by schedule_maker prompt."""

    day_name: str
    focus: str
    recovery_hours_after_day: int = Field(ge=12, le=96)
    warmup_note: str | None = None
    cooldown_note: str | None = None


class ScheduleMakerOutput(BaseModel):
    """Structured output for scheduling decisions."""

    day_templates: list[DayTemplate] = Field(default_factory=list)
    coach_notes: list[str] = Field(default_factory=list)

    @field_validator("coach_notes", mode="before")
    @classmethod
    def _coerce_coach_notes(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise TypeError("coach_notes must be a string or a list of strings")


def _build_default_day_templates(days_per_week: int) -> list[DayTemplate]:
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    templates: list[DayTemplate] = []
    if days_per_week >= 4:
        focus_sequence = ["Upper Body", "Lower Body", "Push", "Pull"]
        name_sequence = ["Monday", "Tuesday", "Thursday", "Saturday"]
    elif days_per_week == 3:
        focus_sequence = ["Full Body A", "Upper Body", "Lower Body"]
        name_sequence = ["Monday", "Wednesday", "Friday"]
    else:
        focus_sequence = ["Full Body", "Conditioning"]
        name_sequence = names

    for index in range(days_per_week):
        focus = focus_sequence[index % len(focus_sequence)]
        templates.append(
            DayTemplate(
                day_name=name_sequence[index],
                focus=focus,
                recovery_hours_after_day=48 if "Lower" in focus or "Leg" in focus else 36,
                warmup_note="5-10 min dynamic warm-up focused on the primary joints used today.",
                cooldown_note="Finish with light mobility and easy breathing for 3-5 minutes.",
            )
        )
    return templates


def _normalize_day_templates(
    day_templates: list[DayTemplate], days_per_week: int
) -> list[DayTemplate]:
    if len(day_templates) != days_per_week:
        return _build_default_day_templates(days_per_week)

    generic_focuses = {"lower body strength", "upper body strength", "full body", "active recovery"}
    template_focuses = {template.focus.strip().lower() for template in day_templates}
    if len(template_focuses) < min(days_per_week, 3):
        return _build_default_day_templates(days_per_week)
    if template_focuses.issubset(generic_focuses) and days_per_week >= 4:
        return _build_default_day_templates(days_per_week)
    return day_templates


def categorize_exercise(exercise_name: str) -> str:
    """Categorize exercise by name matching."""

    name_lower = exercise_name.lower()
    for category, keywords in MOVEMENT_CATEGORIES.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    return "core"


def enforce_day_routing(
    day_focus: str,
    exercises: list[Exercise],
    all_exercises: list[Exercise],
) -> list[Exercise]:
    """Filter exercises to match the day focus and supplement deterministically."""

    focus_lower = day_focus.lower()
    if "push" in focus_lower:
        allowed = {"push"}
    elif "pull" in focus_lower:
        allowed = {"pull"}
    elif "lower" in focus_lower or "leg" in focus_lower:
        allowed = {"lower"}
    elif "upper" in focus_lower:
        allowed = {"push", "pull"}
    else:
        allowed = {"push", "pull", "lower", "core", "cardio"}

    filtered = [exercise for exercise in exercises if categorize_exercise(exercise.name) in allowed]

    if "lower" in focus_lower or "leg" in focus_lower:
        filtered = [
            exercise
            for exercise in filtered
            if categorize_exercise(exercise.name) not in {"push", "pull"}
        ]

    if "full" not in focus_lower:
        core_exercises = [
            exercise
            for exercise in all_exercises
            if categorize_exercise(exercise.name) == "core" and exercise not in filtered
        ]
        if core_exercises:
            filtered.append(core_exercises[0])

    if len(filtered) < 4:
        supplements = [
            exercise
            for exercise in all_exercises
            if categorize_exercise(exercise.name) in allowed and exercise not in filtered
        ]
        filtered.extend(supplements[: 4 - len(filtered)])

    return filtered[:6]


def _chunk_exercises_by_day(
    day_templates: list[DayTemplate],
    requested_weeks: int,
    selected: list,
) -> list[WeekPlan]:
    if not day_templates:
        return []

    per_day = max(min(len(selected) // max(len(day_templates), 1), 7), 5)
    weeks: list[WeekPlan] = []

    def build_day_prescriptions(
        template: DayTemplate, day_index: int, week_number: int
    ) -> list[ExercisePrescription]:
        ranked = enforce_day_routing(template.focus, selected, selected)

        offset = (week_number - 1) * len(day_templates) + day_index
        rotated = ranked[offset % len(ranked) :] + ranked[: offset % len(ranked)]
        prescriptions: list[ExercisePrescription] = []
        used_ids: set[str] = set()
        for exercise in rotated:
            if len(prescriptions) >= per_day:
                break
            if exercise.exercise_id in used_ids:
                continue
            used_ids.add(exercise.exercise_id)
            sets = (
                4 if template.focus in {"Upper Body", "Lower Body", "Push", "Pull", "Legs"} else 3
            )
            reps = "6-10" if exercise.category == "strength" else "10-15"
            rest_seconds = 120 if exercise.category == "strength" else 75
            notes: list[str] = []
            if template.warmup_note:
                notes.append(f"Warm-up: {template.warmup_note}")
            if template.cooldown_note:
                notes.append(f"Cool-down: {template.cooldown_note}")
            prescriptions.append(
                ExercisePrescription(
                    exercise_id=exercise.exercise_id,
                    exercise_name=exercise.name,
                    sets=sets,
                    reps=reps,
                    rest_seconds=rest_seconds,
                    target_rpe=7.0 if sets == 4 else 6.5,
                    notes=" ".join(notes) if notes else None,
                )
            )
        return prescriptions

    for week in range(1, requested_weeks + 1):
        day_plans: list[DayPlan] = []
        for day_index, template in enumerate(day_templates):
            prescriptions = build_day_prescriptions(template, day_index, week)

            day_plans.append(
                DayPlan(
                    day_name=template.day_name,
                    focus=template.focus,
                    recovery_hours_after_day=template.recovery_hours_after_day,
                    exercises=prescriptions,
                )
            )

        weeks.append(WeekPlan(week_number=week, days=day_plans))

    return weeks


async def run(state: AgentState) -> AgentState:
    """Create weekly schedule and exercise distribution."""

    agent = "schedule_maker"
    await log_agent_event(state, agent=agent, event="started")

    profile = state["user_profile"]
    selected_exercises = state["candidate_exercises"]

    if profile is None:
        append_error(state, agent=agent, message="User profile is missing")
        return state
    if not selected_exercises:
        append_error(state, agent=agent, message="No selected exercises available for scheduling")
        return state

    output = await call_structured_llm(
        state,
        agent=agent,
        system_prompt=SCHEDULE_MAKER_PROMPT,
        payload={
            "days_per_week": profile.availability.days_per_week,
            "preferred_days": profile.availability.preferred_days,
            "experience_level": profile.experience_level,
            "selected_exercises": [
                exercise.model_dump(mode="python") for exercise in selected_exercises
            ],
        },
        output_model=ScheduleMakerOutput,
        record_error_on_failure=False,
    )

    day_templates = (
        output.day_templates
        if output and output.day_templates
        else _build_default_day_templates(profile.availability.days_per_week)
    )
    day_templates = _normalize_day_templates(day_templates, profile.availability.days_per_week)
    weekly_schedule = _chunk_exercises_by_day(
        day_templates, state["requested_weeks"], selected_exercises
    )

    if not weekly_schedule:
        append_error(state, agent=agent, message="Schedule generation produced no week plans")
        return state

    state["weekly_schedule"] = weekly_schedule
    state["plan_context"]["coach_notes"] = output.coach_notes if output else []

    await log_agent_event(
        state,
        agent=agent,
        event="completed",
        payload={"weeks": len(weekly_schedule), "days_per_week": len(weekly_schedule[0].days)},
    )
    return state
