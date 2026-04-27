"""Agent 8: assemble and persist final structured plan output."""

from __future__ import annotations

from uuid import uuid4

from workout_agent.agents.common import log_agent_event
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import (
    EvidenceSource,
    ResolvedConstraintSummary,
    SafetyAssessment,
    WorkoutPlan,
)


def _build_constraint_summary(state: AgentState) -> list[ResolvedConstraintSummary]:
    return [
        ResolvedConstraintSummary(
            condition_id=constraint.condition_id,
            canonical_name=constraint.canonical_name,
            condition_type=constraint.condition_type,
            movement_restrictions=constraint.movement_restrictions,
            safe_alternatives=constraint.safe_alternatives,
            affected_body_parts=constraint.affected_body_parts,
            evidence_level=constraint.evidence_level,
        )
        for constraint in state["resolved_constraints"]
    ]


def _build_evidence_references(state: AgentState) -> list[EvidenceSource]:
    seen: set[tuple[str, str | None, int | None]] = set()
    references: list[EvidenceSource] = []
    for constraint in state["resolved_constraints"]:
        for source in constraint.sources:
            key = (source.title, source.url, source.year)
            if key in seen:
                continue
            seen.add(key)
            references.append(source)
    return references


async def run(state: AgentState) -> AgentState:
    """Build final WorkoutPlan object and persist to MongoDB."""

    agent = "plan_export"
    await log_agent_event(state, agent=agent, event="started")

    profile = state["user_profile"]
    if profile is None:
        append_error(state, agent=agent, message="User profile is missing")
        return state

    if not state["weekly_schedule"]:
        append_error(state, agent=agent, message="Weekly schedule is missing")
        return state

    safety_assessment = state["safety_assessment"] or SafetyAssessment()
    status = "approved"
    if safety_assessment.has_critical_issues:
        status = "needs_review"
    elif any(issue.severity in {"high", "critical"} for issue in safety_assessment.issues):
        status = "needs_review"
    if state["errors"]:
        status = "needs_review" if status == "approved" else status

    final_plan = WorkoutPlan(
        plan_id=str(uuid4()),
        request_id=state["request_id"],
        user_id=profile.user_id,
        weeks=state["requested_weeks"],
        weekly_schedule=state["weekly_schedule"],
        progression_targets=state["progression_targets"],
        safety_assessment=safety_assessment,
        constraint_summary=_build_constraint_summary(state),
        evidence_references=_build_evidence_references(state),
        explanations=state["explanations"],
        status=status,
        metadata={
            "training_style": state["plan_context"].get("training_style", "balanced"),
            "risk_retry_count": state["risk_retry_count"],
            "error_count": len(state["errors"]),
            "blocked_exercise_count": len(state["blocked_exercise_ids"]),
            "resolved_constraint_count": len(state["resolved_constraints"]),
        },
    )

    state["final_plan"] = final_plan
    plan_repo = state["runtime"]["workout_plan_repository"]
    try:
        await plan_repo.save_plan(final_plan)
    except Exception as exc:
        append_error(
            state,
            agent=agent,
            message="Failed to persist final workout plan",
            details=str(exc),
        )

    await log_agent_event(
        state,
        agent=agent,
        event="completed",
        payload={"plan_id": final_plan.plan_id, "status": final_plan.status},
    )
    return state
