"""Agent 6: safety gate for candidate workout plan."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from workout_agent.agents.common import call_structured_llm, log_agent_event
from workout_agent.agents.prompts import RISK_ASSESSMENT_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import SafetyAssessment, SafetyIssue


def _slugify_exercise_name(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace("-", " ")
        .replace("/", " ")
        .replace("  ", " ")
        .replace(" ", "_")
    )


class RiskAssessmentOutput(BaseModel):
    """Structured risk assessment output."""

    model_config = ConfigDict(extra="ignore")

    has_critical_issues: bool = False
    issues: list[SafetyIssue] = Field(default_factory=list)
    validated_exercises: list[str] = Field(default_factory=list)
    overall_safety_score: float = 0.85


def _safe_fallback_assessment(state: AgentState) -> RiskAssessmentOutput:
    validated = [
        prescription.exercise_name
        for week in state["weekly_schedule"]
        for day in week.days
        for prescription in day.exercises
    ]
    return RiskAssessmentOutput(
        has_critical_issues=False,
        issues=[],
        validated_exercises=validated,
        overall_safety_score=0.85,
    )


def _rule_based_safety_scan(state: AgentState) -> list[SafetyIssue]:
    constraints = state["constraints"]
    if constraints is None:
        return []

    contraindications = {item.lower() for item in constraints.contraindications}
    issues: list[SafetyIssue] = []

    for week in state["weekly_schedule"]:
        for day in week.days:
            for prescription in day.exercises:
                tokenized = {
                    part.strip().lower()
                    for part in prescription.exercise_name.replace("-", " ")
                    .replace("/", " ")
                    .split()
                }
                overlap = contraindications.intersection(tokenized)
                if overlap:
                    issues.append(
                        SafetyIssue(
                            exercise_name=prescription.exercise_name,
                            reason=f"Potential conflict with contraindication(s): {', '.join(sorted(overlap))}",
                            severity="critical",
                            recommendation="Replace with a safer movement pattern.",
                        )
                    )
    return issues


async def run(state: AgentState) -> AgentState:
    """Validate schedule safety and trigger re-selection loop when needed."""

    agent = "risk_assessment"
    await log_agent_event(state, agent=agent, event="started")

    if not state["weekly_schedule"]:
        append_error(state, agent=agent, message="Weekly schedule is missing for risk assessment")
        return state

    llm_output = await call_structured_llm(
        state,
        agent=agent,
        system_prompt=RISK_ASSESSMENT_PROMPT,
        payload={
            "constraints": state["constraints"].model_dump(mode="python")
            if state["constraints"]
            else {},
            "weekly_schedule": [
                week.model_dump(mode="python") for week in state["weekly_schedule"]
            ],
            "existing_risk_flags": state["plan_context"].get("risk_flags", []),
        },
        output_model=RiskAssessmentOutput,
        record_error_on_failure=False,
    )

    if llm_output is None:
        llm_output = _safe_fallback_assessment(state)

    rule_issues = _rule_based_safety_scan(state)
    llm_issues = llm_output.issues if llm_output else []

    merged_issues: list[SafetyIssue] = []
    seen_keys: set[tuple[str, str]] = set()
    for issue in [*llm_issues, *rule_issues]:
        key = (issue.exercise_name.lower(), issue.reason.lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged_issues.append(issue)

    has_critical = llm_output.has_critical_issues or any(
        issue.severity == "critical" for issue in merged_issues
    )
    assessment = SafetyAssessment(has_critical_issues=has_critical, issues=merged_issues)
    state["safety_assessment"] = assessment

    exceeded_retry_budget = state["risk_retry_count"] >= state["max_risk_retries"]
    if has_critical and not exceeded_retry_budget:
        blocked_ids = {
            _slugify_exercise_name(issue.exercise_name)
            for issue in merged_issues
            if issue.severity == "critical"
        }
        state["blocked_exercise_ids"] = sorted(
            set(state["blocked_exercise_ids"]).union(blocked_ids)
        )
        state["should_reselect_exercises"] = True
        state["risk_exhausted"] = False
        state["risk_retry_count"] += 1
        await log_agent_event(
            state,
            agent=agent,
            event="critical_issues_detected",
            payload={
                "issues": len(merged_issues),
                "retry_count": state["risk_retry_count"],
                "blocked_exercise_ids": state["blocked_exercise_ids"],
            },
        )
    else:
        state["should_reselect_exercises"] = False
        if has_critical and exceeded_retry_budget:
            state["risk_exhausted"] = True
        else:
            state["risk_exhausted"] = False
        await log_agent_event(
            state,
            agent=agent,
            event="completed",
            payload={
                "issues": len(merged_issues),
                "critical": has_critical,
                "risk_exhausted": state["risk_exhausted"],
            },
        )

    return state
