"""Agent 3: select safe, goal-aligned exercises from the KB."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from workout_agent.agents.common import call_structured_llm, log_agent_event
from workout_agent.agents.prompts import EXERCISE_SELECTOR_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import Exercise


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
    safe_candidates = [
        exercise
        for exercise in candidates
        if _exercise_matches_constraints(exercise, contraindications)
    ]
    if not safe_candidates:
        safe_candidates = candidates

    blocked_ids = {exercise_id.lower() for exercise_id in state["blocked_exercise_ids"]}
    if blocked_ids:
        filtered_candidates = [
            exercise
            for exercise in safe_candidates
            if exercise.exercise_id.lower() not in blocked_ids
        ]
        if filtered_candidates:
            safe_candidates = filtered_candidates

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

    if not selected:
        append_error(state, agent=agent, message="No exercises could be selected")
        return state

    state["candidate_exercises"] = selected
    if output:
        state["plan_context"]["selection_notes"] = output.selection_notes

    await log_agent_event(
        state,
        agent=agent,
        event="completed",
        payload={"selected_count": len(selected)},
    )
    return state
