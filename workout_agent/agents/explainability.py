"""Agent 7: produce human-readable justifications."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from workout_agent.agents.common import call_structured_llm, log_agent_event
from workout_agent.agents.prompts import EXPLAINABILITY_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import DecisionExplanation


class ExplainabilityOutput(BaseModel):
    """Structured explainability output."""

    model_config = ConfigDict(extra="ignore")

    explanations: list[DecisionExplanation] = Field(default_factory=list)


class LlmExplanationItem(BaseModel):
    """Flexible explainability item from the LLM."""

    decision_id: str
    category: str = "general"
    explanation: str

    model_config = ConfigDict(extra="ignore")

    @field_validator("decision_id", mode="before")
    @classmethod
    def _coerce_decision_id(cls, value: object) -> str:
        return str(value)


def _normalize_llm_explanation_output(
    raw_output: ExplainabilityOutput | None,
) -> ExplainabilityOutput | None:
    if raw_output is None:
        return None

    normalized: list[DecisionExplanation] = []
    for item in raw_output.explanations:
        normalized.append(
            DecisionExplanation(
                decision_id=str(item.decision_id),
                title=item.title,
                rationale=item.rationale,
                supporting_factors=item.supporting_factors,
            )
        )
    return ExplainabilityOutput(explanations=normalized)


def _fallback_explanations(state: AgentState) -> list[DecisionExplanation]:
    profile = state["user_profile"]
    constraints = state["constraints"]
    if profile is None:
        return []

    selected_names = [exercise.name for exercise in state["candidate_exercises"][:5]]
    safety_issues = state["safety_assessment"].issues if state["safety_assessment"] else []
    schedule_focuses = [day.focus for week in state["weekly_schedule"][:1] for day in week.days]
    progression_targets = state["progression_targets"]
    constraints_used = []
    if constraints:
        constraints_used = [
            *constraints.injuries,
            *constraints.chronic_conditions,
            *constraints.restrictions,
            *constraints.contraindications,
        ]
    progression_summary = []
    for target in progression_targets[:4]:
        progression_summary.append(
            f"week {target.week_number}: {target.intensity_delta_pct:+.1f}% intensity, {target.load_adjustment_kg or 0.0:+.1f} kg, {target.rep_adjustment or 0:+d} reps"
        )

    result = [
        DecisionExplanation(
            decision_id="goal_alignment",
            title="Goal-oriented exercise selection",
            rationale=(
                f"We chose exercises like {', '.join(selected_names[:3])} because they align with your primary goal: "
                f"{state['plan_context'].get('primary_goal', profile.goals[0])}."
            ),
            supporting_factors=[*profile.goals, f"Experience level: {profile.experience_level}"],
        ),
        DecisionExplanation(
            decision_id="exercise_selection",
            title="Exercise selection rationale",
            rationale=(
                f"We selected a mix of movements including {', '.join(selected_names[:4])} so you get compound and accessory work that supports muscle gain while keeping weekly variety higher."
            ),
            supporting_factors=selected_names[:5],
        ),
        DecisionExplanation(
            decision_id="schedule_fit",
            title="Schedule matched to weekly availability",
            rationale=(
                f"We distributed training across {profile.availability.days_per_week} days using a "
                f"{', '.join(schedule_focuses[:4])} split so sessions fit your available time and recovery needs."
            ),
            supporting_factors=[
                f"Session duration target: {profile.availability.minutes_per_session} minutes",
                "Recovery considered in day-level planning",
            ],
        ),
        DecisionExplanation(
            decision_id="progression_strategy",
            title="Progression approach",
            rationale=(
                f"We progress the plan over four weeks with specific week-by-week changes so the workload increases in a controlled way before a deload."
            ),
            supporting_factors=progression_summary,
        ),
    ]

    result.append(
        DecisionExplanation(
            decision_id="safety_screening",
            title="Safety measures applied",
            rationale=(
                "We checked your plan against the constraints you reported and used that information to avoid or flag exercises that could aggravate the affected area."
            ),
            supporting_factors=constraints_used[:5]
            if constraints_used
            else ["No major constraints reported"],
        )
    )

    if safety_issues:
        result.append(
            DecisionExplanation(
                decision_id="risk_review",
                title="Risk review summary",
                rationale=(
                    f"We identified {len(safety_issues)} exercise-specific safety concerns and marked them for review so "
                    "you can swap or modify them before training."
                ),
                supporting_factors=[issue.exercise_name for issue in safety_issues[:4]],
            )
        )

    return result


async def run(state: AgentState) -> AgentState:
    """Generate final rationale entries for major plan decisions."""

    agent = "explainability"
    await log_agent_event(state, agent=agent, event="started")

    profile = state["user_profile"]
    if profile is None:
        append_error(state, agent=agent, message="User profile is missing")
        return state

    output = await call_structured_llm(
        state,
        agent=agent,
        system_prompt=EXPLAINABILITY_PROMPT,
        payload={
            "user_profile": profile.model_dump(mode="python"),
            "constraints": state["constraints"].model_dump(mode="python")
            if state["constraints"]
            else {},
            "candidate_exercises": [
                exercise.model_dump(mode="python") for exercise in state["candidate_exercises"]
            ],
            "weekly_schedule": [
                week.model_dump(mode="python") for week in state["weekly_schedule"]
            ],
            "progression_targets": [
                target.model_dump(mode="python") for target in state["progression_targets"]
            ],
            "safety_assessment": (
                state["safety_assessment"].model_dump(mode="python")
                if state["safety_assessment"]
                else {}
            ),
        },
        output_model=ExplainabilityOutput,
        temperature=0.3,
        record_error_on_failure=False,
    )
    output = _normalize_llm_explanation_output(output)

    explanations = (
        output.explanations if output and output.explanations else _fallback_explanations(state)
    )
    if not explanations:
        append_error(state, agent=agent, message="No explanations were generated")
        return state

    state["explanations"] = explanations
    await log_agent_event(
        state,
        agent=agent,
        event="completed",
        payload={"explanation_count": len(explanations)},
    )
    return state
