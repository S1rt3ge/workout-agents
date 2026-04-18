"""Agent 2: normalize constraints and derive contraindications."""

from __future__ import annotations

from pydantic import BaseModel, Field

from workout_agent.agents.common import call_structured_llm, log_agent_event, unique_preserve_order
from workout_agent.agents.prompts import CONSTRAINT_RECEIVER_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import ConstraintProfile


class ConstraintReceiverOutput(BaseModel):
    """Structured output expected from constraints normalization."""

    normalized_injuries: list[str] = Field(default_factory=list)
    normalized_conditions: list[str] = Field(default_factory=list)
    normalized_restrictions: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    affected_body_parts: list[str] = Field(default_factory=list)
    movement_restrictions: list[str] = Field(default_factory=list)
    safe_alternatives: list[str] = Field(default_factory=list)


async def run(state: AgentState) -> AgentState:
    """Normalize constraints and prepare safety hints for downstream agents."""

    agent = "constraint_receiver"
    await log_agent_event(state, agent=agent, event="started")

    constraints = state["constraints"] or ConstraintProfile()
    output = await call_structured_llm(
        state,
        agent=agent,
        system_prompt=CONSTRAINT_RECEIVER_PROMPT,
        payload={"constraints": constraints.model_dump(mode="python")},
        output_model=ConstraintReceiverOutput,
    )

    if output is not None:
        merged_contraindications = unique_preserve_order(
            constraints.contraindications
            + output.contraindications
            + output.normalized_restrictions
        )
        state["constraints"] = constraints.model_copy(
            update={
                "injuries": unique_preserve_order(
                    constraints.injuries + output.normalized_injuries
                ),
                "chronic_conditions": unique_preserve_order(
                    constraints.chronic_conditions + output.normalized_conditions
                ),
                "restrictions": unique_preserve_order(
                    constraints.restrictions + output.normalized_restrictions
                ),
                "contraindications": merged_contraindications,
            }
        )
        state["plan_context"]["risk_flags"] = output.risk_flags
        state["plan_context"]["affected_body_parts"] = output.affected_body_parts
        state["plan_context"]["movement_restrictions"] = output.movement_restrictions
        state["plan_context"]["safe_alternatives"] = output.safe_alternatives
    else:
        state["constraints"] = constraints
        state["plan_context"].setdefault("risk_flags", [])
        state["plan_context"].setdefault("affected_body_parts", [])
        state["plan_context"].setdefault("movement_restrictions", [])
        state["plan_context"].setdefault("safe_alternatives", [])

    if state["constraints"] is None:
        append_error(
            state, agent=agent, message="Constraint normalization produced an empty profile"
        )

    await log_agent_event(
        state,
        agent=agent,
        event="completed",
        payload={"contraindication_count": len(state["constraints"].contraindications)},
    )
    return state
