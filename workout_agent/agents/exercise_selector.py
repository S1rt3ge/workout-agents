"""Agent 3: select safe, goal-aligned exercises from the KB."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from workout_agent.agents.common import call_structured_llm, log_agent_event, normalize_free_text
from workout_agent.agents.prompts import EXERCISE_SELECTOR_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import ConstraintProfile, Exercise, MedicalConstraint


class ExerciseSelectorOutput(BaseModel):
    """Structured exercise selection output."""

    selected_exercise_ids: list[str] = Field(default_factory=list)
    selection_notes: list[str] = Field(default_factory=list)

    @field_validator("selection_notes", mode="before")
    @classmethod
    def _coerce_selection_notes(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise TypeError("selection_notes must be a string or a list of strings")


ROUTING_KEYWORDS: dict[str, tuple[str, ...]] = {
    "push": (
        "bench press",
        "chest press",
        "machine chest",
        "cable fly",
        "chest",
        "pec",
        "push-up",
        "pushup",
        "overhead press",
        "shoulder press",
        "lateral raise",
        "tricep",
        "pushdown",
        "extension",
        "dip",
        "incline",
        "decline",
        "fly",
    ),
    "pull": (
        "row",
        "pull-up",
        "pullup",
        "chin-up",
        "chinup",
        "lat pulldown",
        "face pull",
        "rear delt",
        "reverse pec",
        "cable pull",
        "pullover",
        "curl",
        "shrug",
    ),
    "lower": (
        "squat",
        "deadlift",
        "leg press",
        "leg curl",
        "leg extension",
        "hack squat",
        "split squat",
        "lunge",
        "reverse lunge",
        "bulgarian",
        "calf",
        "hip thrust",
        "glute bridge",
    ),
}

SHOULDER_SENSITIVE_KEYWORDS = (
    "overhead press",
    "shoulder press",
    "arnold press",
    "lateral raise",
    "upright row",
    "push press",
    "overhead tricep extension",
)


def _categorize_for_routing(exercise: Exercise) -> str:
    name_lower = exercise.name.lower()
    if any(keyword in name_lower for keyword in ("face pull", "rear delt", "reverse pec")):
        return "pull"
    if any(
        keyword in name_lower
        for keyword in (
            "leg press",
            "leg curl",
            "leg extension",
            "split squat",
            "bulgarian",
            "lunge",
            "squat",
            "deadlift",
            "hip thrust",
            "glute bridge",
            "calf",
        )
    ):
        return "lower"
    for category, keywords in ROUTING_KEYWORDS.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    return "other"


def _is_shoulder_sensitive_exercise(exercise: Exercise) -> bool:
    name_lower = exercise.name.lower()
    return any(keyword in name_lower for keyword in SHOULDER_SENSITIVE_KEYWORDS)


def _select_matching(
    exercises: list[Exercise],
    *,
    include_keywords: tuple[str, ...],
    exclude_ids: set[str],
) -> Exercise | None:
    for exercise in exercises:
        if exercise.exercise_id in exclude_ids:
            continue
        name_lower = exercise.name.lower()
        if any(keyword in name_lower for keyword in include_keywords):
            return exercise
    return None


def _has_matching_exercise(exercises: list[Exercise], keywords: tuple[str, ...]) -> bool:
    return _select_matching(exercises, include_keywords=keywords, exclude_ids=set()) is not None


def _has_knee_constraint(constraints: ConstraintProfile | None) -> bool:
    if constraints is None:
        return False

    values = [
        *constraints.injuries,
        *constraints.chronic_conditions,
        *constraints.restrictions,
        *constraints.contraindications,
    ]
    normalized_values = [
        str(value).strip().lower().replace("-", "_").replace(" ", "_")
        for value in values
    ]
    return any("knee_injury" in value or "knee_pain" in value for value in normalized_values)


def _constraint_text(constraints: ConstraintProfile | None) -> str:
    if constraints is None:
        return ""

    values = [
        *constraints.injuries,
        *constraints.chronic_conditions,
        *constraints.restrictions,
        *constraints.contraindications,
    ]
    return " ".join(str(value).lower().replace("-", "_") for value in values)


def _has_shoulder_constraint(constraints: ConstraintProfile | None) -> bool:
    text = _constraint_text(constraints)
    return "shoulder" in text or "overhead press" in text or "lateral raise" in text


def _has_pressure_constraint(constraints: ConstraintProfile | None) -> bool:
    text = _constraint_text(constraints)
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
            "high_pressure",
        )
    )


def _required_coverage_keywords(constraints: ConstraintProfile | None) -> list[tuple[str, ...]]:
    keywords = [
        ("lat pulldown", "pull-up", "pullup", "chin-up", "chinup"),
        ("face pull", "rear delt", "reverse pec"),
        ("cable tricep pushdown", "tricep pushdown", "tricep"),
    ]
    if not _has_shoulder_constraint(constraints):
        keywords.append(("lateral raise", "shoulder press", "overhead press"))
    if _has_knee_constraint(constraints):
        keywords.extend(
            [
                ("leg press", "goblet squat"),
                ("hip thrust", "leg curl"),
                ("step-up", "leg extension"),
            ]
        )
    if _has_pressure_constraint(constraints):
        keywords.extend(
            [
                ("leg press", "goblet squat"),
                ("hip thrust", "leg curl"),
                ("seated cable row", "machine seated row", "one-arm dumbbell row"),
            ]
        )
    return keywords


def _ensure_split_coverage(
    selected: list[Exercise],
    candidates: list[Exercise],
    constraints: ConstraintProfile | None,
) -> list[Exercise]:
    push_exercises = [
        exercise for exercise in selected if _categorize_for_routing(exercise) == "push"
    ]
    pull_exercises = [
        exercise for exercise in selected if _categorize_for_routing(exercise) == "pull"
    ]
    lower_exercises = [
        exercise for exercise in selected if _categorize_for_routing(exercise) == "lower"
    ]

    used_ids = {exercise.exercise_id for exercise in selected}
    shoulder_keywords = ("lateral raise", "overhead press", "shoulder press")
    tricep_keywords = ("pushdown", "tricep", "skull crusher", "dip")
    rear_delt_keywords = ("face pull", "rear delt", "reverse pec")
    vertical_pull_keywords = ("lat pulldown", "pull-up", "pullup", "chin-up", "chinup")
    lower_accessory_keywords = (
        "leg extension",
        "leg curl",
        "leg press",
        "split squat",
        "bulgarian",
        "reverse lunge",
        "calf",
    )
    primary_pull_keywords = ("row", "pulldown", "pull-up", "pullup", "face pull", "rear delt")

    supplements: list[Exercise] = []
    if not _has_shoulder_constraint(constraints) and not any(
        any(keyword in exercise.name.lower() for keyword in shoulder_keywords)
        for exercise in push_exercises
    ):
        replacement = _select_matching(
            candidates,
            include_keywords=shoulder_keywords,
            exclude_ids=used_ids,
        )
        if replacement is not None:
            supplements.append(replacement)
            used_ids.add(replacement.exercise_id)

    if not any(
        any(keyword in exercise.name.lower() for keyword in tricep_keywords)
        for exercise in push_exercises
    ):
        tricep_candidates = candidates
        if _has_shoulder_constraint(constraints):
            tricep_candidates = [
                exercise
                for exercise in candidates
                if not _is_shoulder_sensitive_exercise(exercise)
            ]
        replacement = _select_matching(
            tricep_candidates,
            include_keywords=tricep_keywords,
            exclude_ids=used_ids,
        )
        if replacement is not None:
            supplements.append(replacement)
            used_ids.add(replacement.exercise_id)

    if not any(
        any(keyword in exercise.name.lower() for keyword in vertical_pull_keywords)
        for exercise in pull_exercises
    ):
        replacement = _select_matching(
            candidates,
            include_keywords=vertical_pull_keywords,
            exclude_ids=used_ids,
        )
        if replacement is not None:
            supplements.append(replacement)
            used_ids.add(replacement.exercise_id)
            pull_exercises.append(replacement)

    if not any(
        any(keyword in exercise.name.lower() for keyword in rear_delt_keywords)
        for exercise in pull_exercises
    ):
        replacement = _select_matching(
            candidates,
            include_keywords=rear_delt_keywords,
            exclude_ids=used_ids,
        )
        if replacement is not None:
            supplements.append(replacement)
            used_ids.add(replacement.exercise_id)
            pull_exercises.append(replacement)

    primary_pull_count = sum(
        1
        for exercise in pull_exercises
        if any(keyword in exercise.name.lower() for keyword in primary_pull_keywords)
    )
    while primary_pull_count < 3:
        replacement = _select_matching(
            candidates,
            include_keywords=primary_pull_keywords,
            exclude_ids=used_ids,
        )
        if replacement is None:
            break
        supplements.append(replacement)
        used_ids.add(replacement.exercise_id)
        pull_exercises.append(replacement)
        primary_pull_count += 1

    while len(pull_exercises) < 4:
        replacement = _select_matching(
            candidates,
            include_keywords=ROUTING_KEYWORDS["pull"],
            exclude_ids=used_ids,
        )
        if replacement is None:
            break
        supplements.append(replacement)
        used_ids.add(replacement.exercise_id)
        pull_exercises.append(replacement)

    lower_accessory_count = sum(
        1
        for exercise in lower_exercises
        if any(keyword in exercise.name.lower() for keyword in lower_accessory_keywords)
    )
    while lower_accessory_count < 2:
        replacement = _select_matching(
            candidates,
            include_keywords=lower_accessory_keywords,
            exclude_ids=used_ids,
        )
        if replacement is None:
            break
        supplements.append(replacement)
        used_ids.add(replacement.exercise_id)
        lower_accessory_count += 1

    if len(lower_exercises) < 5:
        for exercise in candidates:
            if exercise.exercise_id in used_ids:
                continue
            if _categorize_for_routing(exercise) != "lower":
                continue
            supplements.append(exercise)
            used_ids.add(exercise.exercise_id)
            lower_exercises.append(exercise)
            if len(lower_exercises) >= 5:
                break

    return [*selected, *supplements]


def _build_retrieval_query(state: AgentState) -> str:
    profile = state["user_profile"]
    constraints = state["constraints"]
    primary_goal = state["plan_context"].get("primary_goal", "general fitness")
    if profile is None:
        return "safe beginner full body workout"

    parts = [
        f"primary goal: {primary_goal}",
        f"goals: {', '.join(profile.goals)}",
        f"experience: {profile.experience_level}",
        f"equipment: {', '.join(profile.equipment) if profile.equipment else 'minimal equipment'}",
        (
            f"avoid: {', '.join(constraints.contraindications)}"
            if constraints and constraints.contraindications
            else "avoid: none"
        ),
    ]
    return " | ".join(parts)


def _exercise_matches_constraints(exercise: Exercise, contraindications: list[str]) -> bool:
    if not contraindications:
        return True
    exercise_flags = {item.lower() for item in exercise.contraindications}
    normalized_constraints = {item.lower() for item in contraindications}
    if not exercise_flags.isdisjoint(normalized_constraints):
        return False

    def tokenize(values: set[str]) -> set[str]:
        tokens: set[str] = set()
        for value in values:
            parts = value.replace("-", "_").split("_")
            tokens.update(part for part in parts if part)
        return tokens

    exercise_tokens = tokenize(exercise_flags)
    constraint_tokens = tokenize(normalized_constraints)
    conflict_tokens = {
        "knee",
        "shoulder",
        "back",
        "ankle",
        "wrist",
        "hip",
        "hamstring",
        "elbow",
        "neck",
    }
    return exercise_tokens.intersection(conflict_tokens).isdisjoint(
        constraint_tokens.intersection(conflict_tokens)
    )


def _body_part_conflicts(exercise: Exercise, body_parts: list[str]) -> bool:
    if not body_parts:
        return False

    searchable_text = normalize_free_text(
        " ".join([exercise.name, *exercise.primary_muscles, *exercise.secondary_muscles])
    )
    for body_part in body_parts:
        normalized_body_part = normalize_free_text(body_part)
        if not normalized_body_part:
            continue
        body_tokens = set(normalized_body_part.split())
        if body_tokens and body_tokens.issubset(set(searchable_text.split())):
            return True
    return False


def _constraint_blocks_exercise(
    exercise: Exercise,
    constraint: MedicalConstraint,
) -> tuple[bool, str | None]:
    exercise_name = normalize_free_text(exercise.name)
    contraindication_text = normalize_free_text(" ".join(exercise.contraindications))

    for keyword in constraint.contraindicated_exercise_keywords:
        normalized_keyword = normalize_free_text(keyword)
        if normalized_keyword and normalized_keyword in exercise_name:
            return True, f"keyword:{keyword}"
        if normalized_keyword and normalized_keyword in contraindication_text:
            return True, f"contraindication:{keyword}"

    if _body_part_conflicts(exercise, constraint.affected_body_parts):
        return True, f"body_part:{constraint.canonical_name}"

    return False, None


def _apply_hard_safety_filter(
    exercises: list[Exercise],
    resolved_constraints: list[MedicalConstraint],
) -> tuple[list[Exercise], list[dict[str, str]]]:
    safe: list[Exercise] = []
    blocked: list[dict[str, str]] = []

    for exercise in exercises:
        conflict_reason: dict[str, str] | None = None
        for constraint in resolved_constraints:
            blocked_by_constraint, reason = _constraint_blocks_exercise(exercise, constraint)
            if blocked_by_constraint:
                conflict_reason = {
                    "exercise_id": exercise.exercise_id,
                    "exercise_name": exercise.name,
                    "condition_id": constraint.condition_id,
                    "canonical_name": constraint.canonical_name,
                    "reason": reason or "knowledge_base_filter",
                }
                break

        if conflict_reason is not None:
            blocked.append(conflict_reason)
            continue
        safe.append(exercise)

    return safe, blocked


def _build_diverse_selection(
    exercises: list[Exercise],
    *,
    min_count: int,
    max_count: int,
) -> list[Exercise]:
    if not exercises:
        return []

    selected: list[Exercise] = []
    seen_ids: set[str] = set()
    muscle_counts: dict[str, int] = {}

    prioritized = sorted(
        exercises,
        key=lambda exercise: (
            len(exercise.primary_muscles),
            1 if exercise.category == "strength" else 0,
            1 if exercise.difficulty in {"beginner", "intermediate"} else 0,
            exercise.score or 0.0,
        ),
        reverse=True,
    )

    for exercise in prioritized:
        if len(selected) >= max_count:
            break
        if exercise.exercise_id in seen_ids:
            continue

        primary_groups = exercise.primary_muscles or ["general"]
        least_covered = min(muscle_counts.get(group, 0) for group in primary_groups)
        if least_covered > 1 and len(selected) >= min_count:
            continue

        selected.append(exercise)
        seen_ids.add(exercise.exercise_id)
        for group in primary_groups:
            muscle_counts[group] = muscle_counts.get(group, 0) + 1

    if len(selected) < min_count:
        for exercise in prioritized:
            if len(selected) >= min_count:
                break
            if exercise.exercise_id in seen_ids:
                continue
            selected.append(exercise)
            seen_ids.add(exercise.exercise_id)

    return selected[:max_count]


async def run(state: AgentState) -> AgentState:
    """Retrieve exercise candidates and select final exercise subset."""

    agent = "exercise_selector"
    await log_agent_event(
        state,
        agent=agent,
        event="started",
        payload={"retry_count": state["risk_retry_count"]},
    )

    profile = state["user_profile"]
    constraints = state["constraints"]
    resolved_constraints = state["resolved_constraints"]
    if profile is None:
        append_error(state, agent=agent, message="User profile is missing")
        return state

    runtime = state["runtime"]
    settings = runtime["settings"]
    exercise_repo = runtime["exercise_repository"]
    ollama = runtime["ollama_client"]

    retrieval_filters: dict[str, object] = {}
    if profile.equipment:
        retrieval_filters["equipment"] = {"$in": profile.equipment}

    candidates: list[Exercise] = []
    retrieval_query = _build_retrieval_query(state)
    vector_failure: Exception | None = None
    if settings.use_vector_search:
        try:
            embedding = await ollama.embed(
                model=settings.ollama_embedding_model, text=retrieval_query
            )
            candidates = await exercise_repo.vector_search(
                embedding=embedding,
                limit=max(profile.availability.days_per_week * 6, 12),
                filters=retrieval_filters,
            )
        except Exception as exc:
            vector_failure = exc

    if not settings.use_vector_search or vector_failure is not None:
        try:
            candidates = await exercise_repo.list_exercises(
                limit=max(profile.availability.days_per_week * 8, 16),
                filters=retrieval_filters or None,
            )
            if not candidates and retrieval_filters:
                candidates = await exercise_repo.list_exercises(
                    limit=max(profile.availability.days_per_week * 8, 16),
                    filters=None,
                )
        except Exception as fallback_exc:
            details = str(fallback_exc)
            if vector_failure is not None:
                details = f"vector failure: {vector_failure}; fallback failure: {fallback_exc}"
            append_error(
                state,
                agent=agent,
                message="Exercise retrieval failed",
                details=details,
            )
            return state

    contraindications = constraints.contraindications if constraints else []
    broad_safe_candidates = [
        exercise
        for exercise in candidates
        if _exercise_matches_constraints(exercise, contraindications)
    ]
    if not broad_safe_candidates:
        broad_safe_candidates = candidates

    safe_candidates, blocked_by_knowledge = _apply_hard_safety_filter(
        broad_safe_candidates, resolved_constraints
    )
    state["plan_context"]["knowledge_blocked_exercises"] = blocked_by_knowledge
    if not safe_candidates:
        safe_candidates = broad_safe_candidates

    blocked_ids = {exercise_id.lower() for exercise_id in state["blocked_exercise_ids"]}
    if blocked_ids:
        filtered_candidates = [
            exercise
            for exercise in safe_candidates
            if exercise.exercise_id.lower() not in blocked_ids
        ]
        if filtered_candidates:
            safe_candidates = filtered_candidates

    required_keywords = _required_coverage_keywords(constraints)
    missing_required_coverage = any(
        not _has_matching_exercise(safe_candidates, keywords) for keywords in required_keywords
    )
    if missing_required_coverage:
        try:
            supplemental_candidates = await exercise_repo.list_exercises(limit=80, filters=None)
            supplemental_candidates = [
                exercise
                for exercise in supplemental_candidates
                if _exercise_matches_constraints(exercise, contraindications)
            ]
            supplemental_safe, supplemental_blocked = _apply_hard_safety_filter(
                supplemental_candidates,
                resolved_constraints,
            )
            blocked_by_knowledge = [*blocked_by_knowledge, *supplemental_blocked]
            existing_ids = {exercise.exercise_id.lower() for exercise in safe_candidates}
            required_pool = [
                exercise
                for exercise in supplemental_safe
                if exercise.exercise_id.lower() not in blocked_ids
            ]
            for exercise in required_pool:
                name_lower = exercise.name.lower()
                if exercise.exercise_id.lower() in existing_ids:
                    continue
                if not any(
                    any(keyword in name_lower for keyword in keywords)
                    for keywords in required_keywords
                ):
                    continue
                safe_candidates.append(exercise)
                existing_ids.add(exercise.exercise_id.lower())
        except Exception:
            pass

    if len(safe_candidates) < 10:
        extra_candidates = [
            exercise
            for exercise in candidates
            if exercise.exercise_id.lower() not in blocked_ids and exercise not in safe_candidates
        ]
        safe_candidates = [*safe_candidates, *extra_candidates]

    output = await call_structured_llm(
        state,
        agent=agent,
        system_prompt=EXERCISE_SELECTOR_PROMPT,
        payload={
            "user_profile": profile.model_dump(mode="python"),
            "constraints": constraints.model_dump(mode="python") if constraints else {},
            "resolved_constraints": [
                constraint.model_dump(mode="python") for constraint in resolved_constraints
            ],
            "blocked_exercise_ids": list(blocked_ids),
            "candidate_exercises": [
                exercise.model_dump(mode="python") for exercise in safe_candidates
            ],
        },
        output_model=ExerciseSelectorOutput,
    )

    if output and output.selected_exercise_ids:
        selected_set = {exercise_id.strip().lower() for exercise_id in output.selected_exercise_ids}
        selected = [
            exercise for exercise in safe_candidates if exercise.exercise_id.lower() in selected_set
        ]
    else:
        target_count = max(profile.availability.days_per_week * 4, 10)
        selected = _build_diverse_selection(
            safe_candidates,
            min_count=target_count,
            max_count=min(max(target_count + 4, 12), 20),
        )
        output_notes = ["Fallback deterministic selection used because LLM output was missing."]
        state["plan_context"]["selection_notes"] = output_notes

    if len(selected) < max(profile.availability.days_per_week * 3, 8):
        selected = _build_diverse_selection(
            safe_candidates,
            min_count=max(profile.availability.days_per_week * 3, 8),
            max_count=min(max(profile.availability.days_per_week * 5, 12), 20),
        )

    selected = _ensure_split_coverage(selected, safe_candidates, constraints)

    if not selected:
        append_error(state, agent=agent, message="No exercises could be selected")
        return state

    state["candidate_exercises"] = selected
    if output:
        state["plan_context"]["selection_notes"] = output.selection_notes
    state["plan_context"]["knowledge_filter_count"] = len(blocked_by_knowledge)

    await log_agent_event(
        state,
        agent=agent,
        event="completed",
        payload={
            "selected_count": len(selected),
            "knowledge_filtered_count": len(blocked_by_knowledge),
        },
    )
    return state
