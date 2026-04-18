"""Service layer that executes LangGraph for plan generation."""

from __future__ import annotations

from typing import Any

from workout_agent.core.state import RuntimeDependencies, build_initial_state
from workout_agent.models.api import GeneratePlanRequest, GeneratePlanResponse
from workout_agent.models.domain import AgentError


class WorkoutPlannerService:
    """Application service facade around the LangGraph execution."""

    def __init__(self, *, graph: Any, runtime_dependencies: RuntimeDependencies) -> None:
        self._graph = graph
        self._runtime_dependencies = runtime_dependencies

    async def generate_plan(self, request: GeneratePlanRequest) -> GeneratePlanResponse:
        """Run the full agent pipeline and return API response model."""

        state = build_initial_state(request, runtime=self._runtime_dependencies)

        try:
            final_state = await self._graph.ainvoke(state)
        except Exception as exc:  # pragma: no cover - catastrophic graph failures
            graph_error = AgentError(
                agent="graph", message="Graph execution failed", details=str(exc)
            )
            return GeneratePlanResponse(
                request_id=state["request_id"],
                status="failed",
                plan=None,
                errors=[*state["errors"], graph_error],
            )

        final_plan = final_state.get("final_plan")
        final_errors = final_state.get("errors", [])

        if final_plan is None:
            status = "failed"
        elif final_errors:
            status = "completed_with_issues"
        else:
            status = "completed"

        return GeneratePlanResponse(
            request_id=final_state["request_id"],
            status=status,
            plan=final_plan,
            errors=final_errors,
        )
