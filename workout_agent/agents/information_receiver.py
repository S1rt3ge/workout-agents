"""Agent 1: intake normalization of user profile information."""

from __future__ import annotations

from pydantic import BaseModel, Field

from workout_agent.agents.common import call_structured_llm, log_agent_event, unique_preserve_order
from workout_agent.agents.prompts import INFORMATION_RECEIVER_PROMPT
from workout_agent.core.state import AgentState, append_error


class InformationReceiverOutput(BaseModel):
    """Structured output expected from intake normalization."""

    normalized_goals: list[str] = Field(default_factory=list)
    primary_goal: str | None = None
    training_style: str = "balanced"
    focus_areas: list[str] = Field(default_factory=list)
    intake_notes: str | None = None


def _fallback_information_output(
    state: AgentState, profile_goals: list[str]
) -> InformationReceiverOutput:
    profile = state["user_profile"]
    primary_goal = profile_goals[0] if profile_goals else "general fitness"
    focus_areas = state["plan_context"].get("focus_areas")
    if not isinstance(focus_areas, list):
        focus_areas = []

    experience_level = profile.experience_level if profile is not None else "beginner"
    training_style = "balanced"
    if any("muscle" in goal.lower() or "hypertrophy" in goal.lower() for goal in profile_goals):
        training_style = "strength and hypertrophy"
    elif any("fat" in goal.lower() or "weight loss" in goal.lower() for goal in profile_goals):
        training_style = "metabolic resistance training"
    elif any("endurance" in goal.lower() for goal in profile_goals):
        training_style = "endurance and conditioning"

    if not focus_areas:
        focus_areas = ["full body", "compound lifts", "recovery management"]

    return InformationReceiverOutput(
        normalized_goals=profile_goals,
        primary_goal=primary_goal,
        training_style=training_style,
        focus_areas=focus_areas,
        intake_notes=f"Fallback profile normalization used for {experience_level} user.",
    )


async def run(state: AgentState) -> AgentState:
    """Normalize incoming profile fields and persist user snapshot when available."""

    agent = "information_receiver"
    await log_agent_event(state, agent=agent, event="started")

    profile = state["user_profile"]
    if profile is None:
        append_error(state, agent=agent, message="User profile is missing")
        await log_agent_event(
            state, agent=agent, event="failed", payload={"reason": "missing_profile"}
        )
        return state

    output = await call_structured_llm(
        state,
        agent=agent,
        system_prompt=INFORMATION_RECEIVER_PROMPT,
        payload={"user_profile": profile.model_dump(mode="python")},
        output_model=InformationReceiverOutput,
        record_error_on_failure=False,
    )

    if output is None:
        output = _fallback_information_output(state, profile.goals)

    normalized_goals = unique_preserve_order(output.normalized_goals)
    if not normalized_goals:
        normalized_goals = profile.goals

    state["user_profile"] = profile.model_copy(update={"goals": normalized_goals})
    state["plan_context"].update(
        {
            "primary_goal": output.primary_goal if output.primary_goal else normalized_goals[0],
            "training_style": output.training_style,
            "focus_areas": output.focus_areas,
            "intake_notes": output.intake_notes,
        }
    )

    if profile.user_id:
        user_repo = state["runtime"]["user_repository"]
        try:
            await user_repo.upsert_user_profile(
                profile.user_id, state["user_profile"].model_dump(mode="python")
            )
        except Exception as exc:
            append_error(
                state,
                agent=agent,
                message="Failed to persist user profile snapshot",
                details=str(exc),
            )

    await log_agent_event(
        state,
        agent=agent,
        event="completed",
        payload={
            "goal_count": len(state["user_profile"].goals),
            "primary_goal": state["plan_context"].get("primary_goal"),
        },
    )
    return state
