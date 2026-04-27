"""Agent 6: safety gate for candidate workout plan."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from workout_agent.agents.common import call_structured_llm, log_agent_event, normalize_free_text
from workout_agent.agents.prompts import RISK_ASSESSMENT_PROMPT
from workout_agent.core.state import AgentState, append_error
from workout_agent.models.domain import MedicalConstraint, SafetyAssessment, SafetyIssue


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


def _matches_keyword(text: str, keyword: str) -> bool:
    normalized_text = normalize_free_text(text)
    normalized_keyword = normalize_free_text(keyword)
    return bool(normalized_keyword) and normalized_keyword in normalized_text


def _exercise_matches_body_part(exercise_name: str, condition: MedicalConstraint) -> bool:
    normalized_name = normalize_free_text(exercise_name)
    for body_part in condition.affected_body_parts:
        normalized_part = normalize_free_text(body_part)
        if normalized_part and normalized_part in normalized_name:
            return True
    return False


def _issue_from_condition(
    *,
    prescription_name: str,
    condition: MedicalConstraint,
    reason: str,
    severity: str = "critical",
) -> SafetyIssue:
    recommendation = None
    if condition.safe_alternatives:
        recommendation = f"Prefer: {', '.join(condition.safe_alternatives[:3])}."

    return SafetyIssue(
        exercise_name=prescription_name,
        reason=reason,
        severity=severity,
        recommendation=recommendation,
        condition_id=condition.condition_id,
        condition_name=condition.canonical_name,
        evidence_level=condition.evidence_level,
    )


def _rule_based_safety_scan(state: AgentState) -> list[SafetyIssue]:
    resolved_constraints = state["resolved_constraints"]
    if not resolved_constraints:
        return []

    issues: list[SafetyIssue] = []

    for week in state["weekly_schedule"]:
        for day in week.days:
            for prescription in day.exercises:
                normalized_name = normalize_free_text(prescription.exercise_name)
                for condition in resolved_constraints:
                    keyword_matches = [
                        keyword
                        for keyword in condition.contraindicated_exercise_keywords
                        if _matches_keyword(normalized_name, keyword)
                    ]
                    if keyword_matches:
                        issues.append(
                            _issue_from_condition(
                                prescription_name=prescription.exercise_name,
                                condition=condition,
                                reason=(
                                    "Knowledge base restriction matched contraindicated exercise "
                                    f"keyword(s): {', '.join(keyword_matches)}."
                                ),
                            )
                        )
                        continue

                    movement_matches = [
                        restriction
                        for restriction in condition.movement_restrictions
                        if _matches_keyword(normalized_name, restriction)
                    ]
                    if movement_matches:
                        issues.append(
                            _issue_from_condition(
                                prescription_name=prescription.exercise_name,
                                condition=condition,
                                reason=(
                                    "Knowledge base restriction matched movement restriction(s): "
                                    f"{', '.join(movement_matches)}."
                                ),
                                severity="high",
                            )
                        )
                        continue

                    if _exercise_matches_body_part(prescription.exercise_name, condition):
                        issues.append(
                            _issue_from_condition(
                                prescription_name=prescription.exercise_name,
                                condition=condition,
                                reason=(
                                    "Knowledge base flagged likely loading of affected "
                                    "body part(s): "
                                    f"{', '.join(condition.affected_body_parts)}."
                                ),
                                severity="high",
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
            "resolved_constraints": [
                constraint.model_dump(mode="python") for constraint in state["resolved_constraints"]
            ],
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
        key = (
            issue.exercise_name.lower(),
            issue.reason.lower(),
            (issue.condition_id or "").lower(),
        )
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
