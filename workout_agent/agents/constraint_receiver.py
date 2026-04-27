"""Agent 2: retrieval-first constraint resolution against medical knowledge."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from workout_agent.agents.common import (
    call_structured_llm,
    log_agent_event,
    normalize_free_text,
    unique_preserve_order,
)
from workout_agent.agents.prompts import CONSTRAINT_RECEIVER_PROMPT
from workout_agent.core.state import AgentState
from workout_agent.models.domain import ConstraintProfile, MedicalConstraint


class ConstraintNormalizationOutput(BaseModel):
    """Optional LLM-assisted alias expansion used only for lookup terms."""

    model_config = ConfigDict(extra="ignore")

    normalized_injuries: list[str] = Field(default_factory=list)
    normalized_conditions: list[str] = Field(default_factory=list)
    normalized_restrictions: list[str] = Field(default_factory=list)
    lookup_terms: list[str] = Field(default_factory=list)
    unresolved_flags: list[str] = Field(default_factory=list)

    @field_validator(
        "normalized_injuries",
        "normalized_conditions",
        "normalized_restrictions",
        "lookup_terms",
        "unresolved_flags",
        mode="before",
    )
    @classmethod
    def _coerce_string_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []


def _expand_lookup_terms(terms: list[str]) -> list[str]:
    """Add deterministic fallback aliases for common free-text user phrasing."""

    expanded = list(terms)
    joined = " | ".join(terms)

    shoulder_markers = [
        "shoulder hurts",
        "shoulder pain",
        "strained shoulder",
        "shoulder strain",
        "right shoulder",
        "left shoulder",
    ]
    if any(marker in joined for marker in shoulder_markers):
        expanded.extend(
            [
                "shoulder strain",
                "strained shoulder",
                "shoulder pain",
                "shoulder hurts when pressing",
            ]
        )

    breath_holding_markers = [
        "breath holding",
        "breath-holding",
        "hold breath",
        "valsalva",
        "heavy strength training",
    ]
    if any(marker in joined for marker in breath_holding_markers):
        expanded.extend(
            [
                "avoid valsalva",
                "cannot hold breath under load",
                "breath holding restriction",
                "heavy straining",
            ]
        )

    gi_markers = ["dolichosigmoid", "dolichocolon", "subcompensated form"]
    if any(marker in joined for marker in gi_markers):
        expanded.extend(
            [
                "gi symptoms during training",
                "stomach flare",
                "ibs flare",
            ]
        )

    return unique_preserve_order(expanded)


def _raw_constraint_terms(constraints: ConstraintProfile) -> list[str]:
    return unique_preserve_order(
        [
            *constraints.injuries,
            *constraints.chronic_conditions,
            *constraints.restrictions,
            *constraints.contraindications,
        ]
    )


def _merge_constraint_lists(
    constraints: ConstraintProfile,
    output: ConstraintNormalizationOutput | None,
) -> ConstraintProfile:
    if output is None:
        return constraints

    return constraints.model_copy(
        update={
            "injuries": unique_preserve_order(constraints.injuries + output.normalized_injuries),
            "chronic_conditions": unique_preserve_order(
                constraints.chronic_conditions + output.normalized_conditions
            ),
            "restrictions": unique_preserve_order(
                constraints.restrictions + output.normalized_restrictions
            ),
            "contraindications": unique_preserve_order(constraints.contraindications),
        }
    )


def _build_lookup_terms(
    constraints: ConstraintProfile,
    output: ConstraintNormalizationOutput | None,
) -> list[str]:
    source_terms = _raw_constraint_terms(constraints)
    llm_terms: list[str] = []
    if output is not None:
        llm_terms = [
            *output.lookup_terms,
            *output.normalized_injuries,
            *output.normalized_conditions,
            *output.normalized_restrictions,
        ]

    normalized_terms = [normalize_free_text(value) for value in [*source_terms, *llm_terms]]
    deduplicated = unique_preserve_order([term for term in normalized_terms if term])
    return _expand_lookup_terms(deduplicated)


def _to_medical_constraints(records: list[dict]) -> list[MedicalConstraint]:
    return [MedicalConstraint.model_validate(record) for record in records]


def _summarize_resolved_constraints(
    state: AgentState,
    resolved_constraints: list[MedicalConstraint],
) -> None:
    all_affected_parts = unique_preserve_order(
        [part for constraint in resolved_constraints for part in constraint.affected_body_parts]
    )
    all_restrictions = unique_preserve_order(
        [
            movement
            for constraint in resolved_constraints
            for movement in constraint.movement_restrictions
        ]
    )
    all_safe_alternatives = unique_preserve_order(
        [option for constraint in resolved_constraints for option in constraint.safe_alternatives]
    )
    all_keywords = unique_preserve_order(
        [
            keyword
            for constraint in resolved_constraints
            for keyword in constraint.contraindicated_exercise_keywords
        ]
    )

    state["plan_context"]["affected_body_parts"] = all_affected_parts
    state["plan_context"]["movement_restrictions"] = all_restrictions
    state["plan_context"]["safe_alternatives"] = all_safe_alternatives
    state["plan_context"]["knowledge_based_contraindications"] = all_keywords
    state["plan_context"]["resolved_condition_ids"] = [
        constraint.condition_id for constraint in resolved_constraints
    ]


def _build_constraint_evidence(resolved_constraints: list[MedicalConstraint]) -> list[dict]:
    evidence_rows: list[dict] = []
    for constraint in resolved_constraints:
        evidence_rows.append(
            {
                "condition_id": constraint.condition_id,
                "canonical_name": constraint.canonical_name,
                "evidence_level": constraint.evidence_level,
                "risk_level": constraint.risk_level,
                "sources": [source.model_dump(mode="python") for source in constraint.sources],
            }
        )
    return evidence_rows


async def run(state: AgentState) -> AgentState:
    """Resolve user-reported constraints through structured medical knowledge."""

    agent = "constraint_receiver"
    await log_agent_event(state, agent=agent, event="started")

    constraints = state["constraints"] or ConstraintProfile()
    raw_terms = _raw_constraint_terms(constraints)

    normalization_output: ConstraintNormalizationOutput | None = None
    if raw_terms:
        normalization_output = await call_structured_llm(
            state,
            agent=agent,
            system_prompt=CONSTRAINT_RECEIVER_PROMPT,
            payload={"constraints": constraints.model_dump(mode="python")},
            output_model=ConstraintNormalizationOutput,
            record_error_on_failure=False,
        )

    normalized_constraints = _merge_constraint_lists(constraints, normalization_output)
    lookup_terms = _build_lookup_terms(normalized_constraints, normalization_output)

    repository = state["runtime"]["medical_constraint_repository"]
    matched_records = await repository.find_by_aliases_or_names(lookup_terms)
    resolved_constraints = _to_medical_constraints(matched_records)

    resolved_ids = {constraint.condition_id for constraint in resolved_constraints}
    resolved_terms = {
        normalize_free_text(term)
        for constraint in resolved_constraints
        for term in [
            constraint.condition_id,
            constraint.canonical_name,
            *constraint.aliases,
        ]
    }
    unresolved_terms = [
        term
        for term in lookup_terms
        if term not in resolved_terms and term not in resolved_ids
    ]

    state["constraints"] = normalized_constraints.model_copy(
        update={
            "contraindications": unique_preserve_order(
                normalized_constraints.contraindications
                + [
                    keyword
                    for constraint in resolved_constraints
                    for keyword in constraint.contraindicated_exercise_keywords
                ]
            )
        }
    )
    state["resolved_constraints"] = resolved_constraints
    state["constraint_lookup_terms"] = lookup_terms
    state["constraint_evidence"] = _build_constraint_evidence(resolved_constraints)

    _summarize_resolved_constraints(state, resolved_constraints)

    risk_flags = list(normalization_output.unresolved_flags) if normalization_output else []
    if unresolved_terms:
        warning = (
            "Some reported conditions were not found in the medical knowledge base and were "
            "handled conservatively pending manual caution review."
        )
        state["plan_context"]["constraint_resolution_warning"] = warning
        state["plan_context"]["unresolved_constraints"] = unresolved_terms
        risk_flags.append("manual_caution_required_for_unresolved_constraints")
    else:
        state["plan_context"].pop("constraint_resolution_warning", None)
        state["plan_context"]["unresolved_constraints"] = []

    state["plan_context"]["risk_flags"] = unique_preserve_order(risk_flags)

    if raw_terms and not resolved_constraints:
        state["plan_context"]["constraint_resolution_warning"] = (
            "No reported constraints were resolved from the medical knowledge base. "
            "The plan should be treated with manual caution review."
        )
        state["plan_context"]["unresolved_constraints"] = lookup_terms
        state["plan_context"]["risk_flags"] = unique_preserve_order(
            state["plan_context"].get("risk_flags", [])
            + ["manual_caution_required_for_unresolved_constraints"]
        )

    await log_agent_event(
        state,
        agent=agent,
        event="completed",
        payload={
            "lookup_terms": len(lookup_terms),
            "resolved_constraints": len(resolved_constraints),
            "unresolved_constraints": len(state["plan_context"].get("unresolved_constraints", [])),
        },
    )
    return state
