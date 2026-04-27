"""Agent 4: distribute selected exercises into weekly day plans."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from workout_agent.agents.common import call_structured_llm, log_agent_event, normalize_free_text
from workout_agent.agents.prompts import SCHEDULE_MAKER_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import (
    ConstraintProfile,
    DayPlan,
    Exercise,
    ExercisePrescription,
    MedicalConstraint,
    WeekPlan,
)

PULL_PRIORITY_KEYWORDS = ("face pull", "rear delt", "rear_delt", "reverse pec")
LOWER_PRIORITY_KEYWORDS = (
    "leg press",
    "leg curl",
    "leg extension",
    "split squat",
    "bulgarian",
    "reverse lunge",
    "walking lunge",
    "lunge",
    "squat",
    "deadlift",
    "hip thrust",
    "glute bridge",
    "calf",
)
SHOULDER_SENSITIVE_KEYWORDS = (
    "overhead press",
    "shoulder press",
    "arnold press",
    "lateral raise",
    "upright row",
    "push press",
    "overhead tricep extension",
)
PRESSURE_SENSITIVE_KEYWORDS = (
    "deadlift",
    "barbell back squat",
    "front squat",
    "barbell bent-over row",
    "good morning",
    "kettlebell swing",
    "farmer carry",
    "heavy carry",
    "ab wheel",
    "plank",
    "burpee",
    "mountain climber",
    "box jump",
    "jump rope",
)

MOVEMENT_CATEGORIES = {
    "push": [
        "bench press",
        "chest press",
        "machine chest",
        "chest fly",
        "cable fly",
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
        "incline",
        "decline",
        "chest",
        "pec",
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
        "reverse pec",
        "t-bar",
        "cable pull",
    ],
    "lower": [
        "squat",
        "deadlift",
        "lunge",
        "reverse lunge",
        "leg press",
        "leg curl",
        "leg extension",
        "hip thrust",
        "glute bridge",
        "calf raise",
        "calf",
        "step-up",
        "split squat",
        "bulgarian",
        "hack squat",
        "sumo",
        "rdl",
        "good morning",
        "wall sit",
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
        focus_sequence = ["Push", "Lower Body", "Pull", "Upper Body"]
        name_sequence = ["Monday", "Tuesday", "Thursday", "Saturday"]
    elif days_per_week == 3:
        focus_sequence = ["Push", "Pull", "Lower Body"]
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
    if days_per_week == 4 and template_focuses == {"upper body", "lower body", "push", "pull"}:
        return _build_default_day_templates(days_per_week)
    if len(template_focuses) < min(days_per_week, 3):
        return _build_default_day_templates(days_per_week)
    if template_focuses.issubset(generic_focuses) and days_per_week >= 4:
        return _build_default_day_templates(days_per_week)
    return day_templates


def categorize_exercise(exercise_name: str) -> str:
    """Categorize exercise by name matching."""

    name_lower = exercise_name.lower()
    if any(keyword in name_lower for keyword in PULL_PRIORITY_KEYWORDS):
        return "pull"
    if any(keyword in name_lower for keyword in LOWER_PRIORITY_KEYWORDS):
        return "lower"
    if "pallof press" in name_lower:
        return "core"
    for category, keywords in MOVEMENT_CATEGORIES.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    return "core"


def _contains_keyword(exercise: Exercise, keywords: tuple[str, ...]) -> bool:
    name_lower = exercise.name.lower()
    return any(keyword in name_lower for keyword in keywords)


def _constraint_text(
    constraints: ConstraintProfile | None,
    resolved_constraints: list[MedicalConstraint] | None = None,
) -> str:
    values: list[str] = []
    if constraints is not None:
        values.extend(
            [
                *constraints.injuries,
                *constraints.chronic_conditions,
                *constraints.restrictions,
                *constraints.contraindications,
            ]
        )
    for constraint in resolved_constraints or []:
        values.extend(
            [
                constraint.condition_id,
                constraint.canonical_name,
                *constraint.affected_body_parts,
                *constraint.movement_restrictions,
                *constraint.safe_alternatives,
                *constraint.contraindicated_exercise_keywords,
            ]
        )

    raw_text = " ".join(str(value).lower() for value in values)
    normalized_text = " ".join(normalize_free_text(str(value)) for value in values)
    underscored_text = " ".join(
        str(value).lower().replace("-", "_").replace(" ", "_") for value in values
    )
    return f"{raw_text} {normalized_text} {underscored_text}"


def _has_shoulder_constraint(
    constraints: ConstraintProfile | None,
    resolved_constraints: list[MedicalConstraint] | None = None,
) -> bool:
    text = _constraint_text(constraints, resolved_constraints)
    return any(
        keyword in text
        for keyword in (
            "shoulder",
            "rotator cuff",
            "rotator_cuff",
            "overhead press",
            "lateral raise",
        )
    )


def _has_pressure_constraint(
    constraints: ConstraintProfile | None,
    resolved_constraints: list[MedicalConstraint] | None = None,
) -> bool:
    text = _constraint_text(constraints, resolved_constraints)
    return any(
        keyword in text
        for keyword in (
            "breath",
            "valsalva",
            "heavy straining",
            "heavy_strength",
            "hernia",
            "abdominal pressure",
            "abdominal_pressure",
            "near maximal",
            "near_maximal",
            "maximal strength",
            "max deadlift",
            "max squat",
            "dolicho",
            "gi symptom",
            "gi_symptom",
            "gi_ibs",
            "ibs",
            "reflux",
            "gerd",
            "symptom flare",
            "high pressure",
            "high_pressure",
        )
    )


def _is_shoulder_sensitive_exercise(exercise: Exercise) -> bool:
    return _contains_keyword(exercise, SHOULDER_SENSITIVE_KEYWORDS)


def _is_pressure_sensitive_exercise(exercise: Exercise) -> bool:
    return _contains_keyword(exercise, PRESSURE_SENSITIVE_KEYWORDS)


def _matches_schedule_constraints(
    exercise: Exercise,
    *,
    shoulder_sensitive: bool,
    pressure_sensitive: bool,
) -> bool:
    if shoulder_sensitive and _is_shoulder_sensitive_exercise(exercise):
        return False
    if pressure_sensitive and _is_pressure_sensitive_exercise(exercise):
        return False
    return True


def _pick_first_matching(
    exercises: list[Exercise],
    *,
    include_keywords: tuple[str, ...],
    exclude_ids: set[str],
) -> Exercise | None:
    for exercise in exercises:
        if exercise.exercise_id in exclude_ids:
            continue
        if _contains_keyword(exercise, include_keywords):
            return exercise
    return None


def _reorder_with_required_exercises(
    exercises: list[Exercise],
    required: list[Exercise],
) -> list[Exercise]:
    required_ids = {exercise.exercise_id for exercise in required}
    ordered_required = [exercise for exercise in required if exercise.exercise_id in required_ids]
    remainder = [exercise for exercise in exercises if exercise.exercise_id not in required_ids]
    return [*ordered_required, *remainder]


def _ensure_push_day_variety(
    filtered: list[Exercise],
    all_exercises: list[Exercise],
    *,
    shoulder_sensitive: bool,
) -> list[Exercise]:
    chest_keywords = (
        "bench press",
        "chest press",
        "machine chest",
        "chest fly",
        "cable fly",
        "push-up",
        "pushup",
        "incline",
        "decline",
        "chest",
        "pec",
    )
    shoulder_keywords = ("lateral raise", "overhead press", "shoulder press", "arnold press")
    tricep_keywords = ("pushdown", "tricep", "skull crusher", "dip", "extension")

    if shoulder_sensitive:
        filtered = [
            exercise for exercise in filtered if not _is_shoulder_sensitive_exercise(exercise)
        ]

    chest_exercises = [
        exercise for exercise in filtered if _contains_keyword(exercise, chest_keywords)
    ]
    non_chest = [exercise for exercise in filtered if exercise not in chest_exercises]
    filtered = [*chest_exercises[:2], *non_chest]

    used_ids = {exercise.exercise_id for exercise in filtered}
    shoulder_exercises = [
        exercise for exercise in filtered if _contains_keyword(exercise, shoulder_keywords)
    ]
    tricep_exercises = [
        exercise for exercise in filtered if _contains_keyword(exercise, tricep_keywords)
    ]

    if not shoulder_sensitive and not shoulder_exercises:
        replacement = _pick_first_matching(
            all_exercises,
            include_keywords=shoulder_keywords,
            exclude_ids=used_ids,
        )
        if replacement is not None:
            filtered.append(replacement)
            used_ids.add(replacement.exercise_id)

    if not tricep_exercises:
        replacement = _pick_first_matching(
            all_exercises,
            include_keywords=("cable tricep pushdown", "tricep pushdown", *tricep_keywords),
            exclude_ids=used_ids,
        )
        if replacement is not None:
            filtered.append(replacement)
            used_ids.add(replacement.exercise_id)

    required_keywords = (
        tricep_keywords if shoulder_sensitive else shoulder_keywords + tricep_keywords
    )
    required = [exercise for exercise in filtered if _contains_keyword(exercise, required_keywords)]
    return _reorder_with_required_exercises(filtered, required)


def _ensure_pull_day_integrity(filtered: list[Exercise]) -> list[Exercise]:
    return [exercise for exercise in filtered if categorize_exercise(exercise.name) == "pull"]


def _ensure_pull_day_variety(
    filtered: list[Exercise],
    all_exercises: list[Exercise],
) -> list[Exercise]:
    filtered = _ensure_pull_day_integrity(filtered)
    used_ids = {exercise.exercise_id for exercise in filtered}
    vertical_pull_keywords = ("lat pulldown", "pull-up", "pullup", "chin-up", "chinup")
    rear_delt_keywords = ("face pull", "rear delt", "reverse pec")

    if not any(_contains_keyword(exercise, vertical_pull_keywords) for exercise in filtered):
        replacement = _pick_first_matching(
            all_exercises,
            include_keywords=vertical_pull_keywords,
            exclude_ids=used_ids,
        )
        if replacement is not None:
            filtered.append(replacement)
            used_ids.add(replacement.exercise_id)

    if not any(_contains_keyword(exercise, rear_delt_keywords) for exercise in filtered):
        replacement = _pick_first_matching(
            all_exercises,
            include_keywords=rear_delt_keywords,
            exclude_ids=used_ids,
        )
        if replacement is not None:
            filtered.append(replacement)
            used_ids.add(replacement.exercise_id)

    if len(filtered) < 4:
        supplements = [
            exercise
            for exercise in all_exercises
            if exercise.exercise_id not in used_ids
            and categorize_exercise(exercise.name) == "pull"
        ]
        filtered.extend(supplements[: 4 - len(filtered)])

    required = [
        exercise
        for exercise in filtered
        if _contains_keyword(exercise, vertical_pull_keywords + rear_delt_keywords)
    ]
    return _reorder_with_required_exercises(filtered, required)


def _has_knee_constraint(
    constraints: ConstraintProfile | None,
    resolved_constraints: list[MedicalConstraint] | None = None,
) -> bool:
    text = _constraint_text(constraints, resolved_constraints)
    return any(
        keyword in text
        for keyword in (
            "knee_injury",
            "knee pain",
            "knee_pain",
            "patellofemoral",
            "anterior knee",
            "anterior_knee",
        )
    )


def _is_knee_sensitive_lower_exercise(exercise: Exercise) -> bool:
    name_lower = exercise.name.lower()
    return any(
        keyword in name_lower
        for keyword in ("barbell back squat", "bulgarian split squat", "lunge")
    )


def _replace_knee_sensitive_lower_exercises(
    filtered: list[Exercise],
    all_exercises: list[Exercise],
) -> list[Exercise]:
    replacement_rules: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
        (("barbell back squat",), ("leg press", "goblet squat")),
        (("bulgarian split squat",), ("hip thrust", "leg curl")),
        (("lunge",), ("step-up", "leg extension")),
    )

    result: list[Exercise] = []
    used_ids: set[str] = set()
    search_pool = [*filtered, *all_exercises]

    for exercise in filtered:
        replacement_keywords: tuple[str, ...] | None = None
        name_lower = exercise.name.lower()
        for blocked_keywords, candidate_keywords in replacement_rules:
            if any(keyword in name_lower for keyword in blocked_keywords):
                replacement_keywords = candidate_keywords
                break

        if replacement_keywords is not None:
            replacement = _pick_first_matching(
                search_pool,
                include_keywords=replacement_keywords,
                exclude_ids=used_ids,
            )
            if replacement is not None:
                result.append(replacement)
                used_ids.add(replacement.exercise_id)
            continue

        if exercise.exercise_id in used_ids:
            continue
        result.append(exercise)
        used_ids.add(exercise.exercise_id)

    return result


def _ensure_lower_day_integrity(
    filtered: list[Exercise],
    all_exercises: list[Exercise],
    *,
    knee_sensitive: bool,
    pressure_sensitive: bool,
) -> list[Exercise]:
    if pressure_sensitive:
        filtered = [
            exercise for exercise in filtered if not _is_pressure_sensitive_exercise(exercise)
        ]

    lower_only = [
        exercise for exercise in filtered if categorize_exercise(exercise.name) == "lower"
    ]
    core_only = [exercise for exercise in filtered if categorize_exercise(exercise.name) == "core"]
    filtered = [*lower_only, *core_only[:1]]
    if knee_sensitive:
        filtered = _replace_knee_sensitive_lower_exercises(filtered, all_exercises)
    used_ids = {exercise.exercise_id for exercise in filtered}

    lower_keywords = (
        "squat",
        "deadlift",
        "leg press",
        "leg curl",
        "leg extension",
        "split squat",
        "bulgarian",
        "lunge",
        "hip thrust",
        "glute bridge",
        "calf",
    )
    supplements = [
        exercise
        for exercise in all_exercises
        if exercise.exercise_id not in used_ids
        and _contains_keyword(exercise, lower_keywords)
        and not (knee_sensitive and _is_knee_sensitive_lower_exercise(exercise))
        and not (pressure_sensitive and _is_pressure_sensitive_exercise(exercise))
    ]
    for exercise in supplements:
        if len(filtered) >= 5:
            break
        filtered.append(exercise)
    return filtered


def enforce_day_routing(
    day_focus: str,
    exercises: list[Exercise],
    all_exercises: list[Exercise],
    *,
    knee_sensitive: bool = False,
    shoulder_sensitive: bool = False,
    pressure_sensitive: bool = False,
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

    candidate_pool = [
        exercise
        for exercise in all_exercises
        if _matches_schedule_constraints(
            exercise,
            shoulder_sensitive=shoulder_sensitive,
            pressure_sensitive=pressure_sensitive,
        )
    ]
    routable_exercises = [
        exercise
        for exercise in exercises
        if _matches_schedule_constraints(
            exercise,
            shoulder_sensitive=shoulder_sensitive,
            pressure_sensitive=pressure_sensitive,
        )
    ]
    filtered = [
        exercise
        for exercise in routable_exercises
        if categorize_exercise(exercise.name) in allowed
    ]

    if "push" in focus_lower:
        filtered = _ensure_push_day_variety(
            filtered,
            candidate_pool,
            shoulder_sensitive=shoulder_sensitive,
        )
    elif "pull" in focus_lower:
        filtered = _ensure_pull_day_variety(filtered, candidate_pool)
    elif "lower" in focus_lower or "leg" in focus_lower:
        filtered = _ensure_lower_day_integrity(
            filtered,
            candidate_pool,
            knee_sensitive=knee_sensitive,
            pressure_sensitive=pressure_sensitive,
        )

    if "upper" in focus_lower:
        core_exercises = [
            exercise
            for exercise in candidate_pool
            if categorize_exercise(exercise.name) == "core" and exercise not in filtered
        ]
        if core_exercises:
            filtered.append(core_exercises[0])

    minimum_count = 5 if ("lower" in focus_lower or "leg" in focus_lower) else 4
    if len(filtered) < minimum_count:
        chest_keywords = (
            "bench press",
            "chest press",
            "machine chest",
            "chest fly",
            "cable fly",
            "push-up",
            "pushup",
            "incline",
            "decline",
            "chest",
            "pec",
        )
        tricep_keywords = ("pushdown", "tricep", "skull crusher", "dip")
        chest_count = sum(1 for exercise in filtered if _contains_keyword(exercise, chest_keywords))

        supplements = [
            exercise
            for exercise in candidate_pool
            if categorize_exercise(exercise.name) in allowed and exercise not in filtered
            and not (
                "push" in focus_lower
                and chest_count >= 2
                and _contains_keyword(exercise, chest_keywords)
                and not _contains_keyword(exercise, tricep_keywords)
            )
            and not (
                knee_sensitive
                and ("lower" in focus_lower or "leg" in focus_lower)
                and _is_knee_sensitive_lower_exercise(exercise)
            )
            and not (
                pressure_sensitive
                and ("lower" in focus_lower or "leg" in focus_lower)
                and _is_pressure_sensitive_exercise(exercise)
            )
        ]
        if "push" in focus_lower:
            supplements = sorted(
                supplements,
                key=lambda exercise: 0 if _contains_keyword(exercise, tricep_keywords) else 1,
            )
        filtered.extend(supplements[: minimum_count - len(filtered)])

    return filtered[:6]


def _chunk_exercises_by_day(
    day_templates: list[DayTemplate],
    requested_weeks: int,
    selected: list[Exercise],
    *,
    knee_sensitive: bool,
    shoulder_sensitive: bool,
    pressure_sensitive: bool,
) -> list[WeekPlan]:
    if not day_templates:
        return []

    per_day = max(min(len(selected) // max(len(day_templates), 1), 7), 5)
    weeks: list[WeekPlan] = []

    def build_day_prescriptions(
        template: DayTemplate, day_index: int, week_number: int
    ) -> list[ExercisePrescription]:
        ranked = enforce_day_routing(
            template.focus,
            selected,
            selected,
            knee_sensitive=knee_sensitive,
            shoulder_sensitive=shoulder_sensitive,
            pressure_sensitive=pressure_sensitive,
        )
        if not ranked:
            return []

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
    resolved_constraints = state["resolved_constraints"]
    weekly_schedule = _chunk_exercises_by_day(
        day_templates,
        state["requested_weeks"],
        selected_exercises,
        knee_sensitive=_has_knee_constraint(state["constraints"], resolved_constraints),
        shoulder_sensitive=_has_shoulder_constraint(state["constraints"], resolved_constraints),
        pressure_sensitive=_has_pressure_constraint(state["constraints"], resolved_constraints),
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
