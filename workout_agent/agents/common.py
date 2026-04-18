"""Shared helpers for agent modules."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from workout_agent.core.state import AgentState, append_error

_ModelT = TypeVar("_ModelT", bound=BaseModel)


def unique_preserve_order(values: list[str]) -> list[str]:
    """Return de-duplicated list preserving first appearance order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(normalized)
    return result


def resolve_model(state: AgentState) -> str:
    """Resolve Ollama model for current request mode."""

    settings = state["runtime"]["settings"]
    return settings.ollama_eval_model if state["use_eval_model"] else settings.ollama_dev_model


async def log_agent_event(
    state: AgentState,
    *,
    agent: str,
    event: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Write agent event to session log, collecting logging errors in state.errors."""

    logger = state["runtime"]["session_log_repository"]
    try:
        await logger.log_event(
            request_id=state["request_id"],
            agent=agent,
            event=event,
            payload=payload,
        )
    except Exception as exc:  # pragma: no cover - logging should never break flow
        append_error(
            state,
            agent=agent,
            message="Failed to persist session log event",
            details=str(exc),
        )


async def call_structured_llm(
    state: AgentState,
    *,
    agent: str,
    system_prompt: str,
    payload: dict[str, Any],
    output_model: type[_ModelT],
    temperature: float = 0.2,
    record_error_on_failure: bool = True,
) -> _ModelT | None:
    """Call Ollama for structured JSON and validate into output_model."""

    runtime = state["runtime"]
    ollama_client = runtime["ollama_client"]
    model = resolve_model(state)

    try:
        response_payload = await ollama_client.chat_json(
            model=model,
            system_prompt=system_prompt,
            user_payload=payload,
            temperature=temperature,
        )
        return output_model.model_validate(response_payload)
    except Exception as exc:
        if record_error_on_failure:
            append_error(
                state,
                agent=agent,
                message="LLM output parsing failed",
                details=str(exc),
            )
        await log_agent_event(
            state,
            agent=agent,
            event="llm_failure",
            payload={"error": str(exc), "model": model},
        )
        return None
