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


def _default_progression(weeks: int) -> list[ProgressionTarget]:
    targets: list[ProgressionTarget] = []
    for week in range(1, weeks + 1):
        deload = week % 4 == 0
        volume_multiplier = 0.9 if deload else min(1.0 + (week - 1) * 0.04, 1.2)
        intensity_delta_pct = -7.5 if deload else min((week - 1) * 2.5, 10.0)
        targets.append(
            ProgressionTarget(
                week_number=week,
                volume_multiplier=volume_multiplier,
                intensity_delta_pct=intensity_delta_pct,
                load_adjustment_kg=0.0 if week == 1 else (2.5 if not deload else 0.0),
                rep_adjustment=0 if week == 1 else (1 if not deload else -2),
                target_rpe=7.0 if week == 1 else (7.5 if not deload else 6.0),
                deload=deload,
                notes="Deload week for recovery" if deload else "Gradual progression",
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

    if not targets:
        append_error(state, agent=agent, message="No progression targets generated")
        return state

    state["progression_targets"] = targets
    await log_agent_event(
        state, agent=agent, event="completed", payload={"target_count": len(targets)}
    )
    return state
