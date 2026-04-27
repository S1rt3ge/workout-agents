"""API routes for workout plan generation."""

# ruff: noqa: B008

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from workout_agent.api.dependencies import get_runtime
from workout_agent.api.schemas import (
    APIResponse,
    ConstraintCatalogItem,
    ConstraintSearchResponse,
    PlanFeedbackRequest,
    PlanFeedbackResponse,
    SessionEvent,
    UserPlanSummary,
)
from workout_agent.models.api import GeneratePlanRequest
from workout_agent.models.domain import MedicalConstraint, WorkoutPlan
from workout_agent.services.runtime import AppRuntime

router = APIRouter(prefix="/v1/plans", tags=["plans"])
users_router = APIRouter(prefix="/v1/users", tags=["users"])
constraints_router = APIRouter(prefix="/v1/constraints", tags=["constraints"])
sessions_router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.post("/generate", response_model=APIResponse[WorkoutPlan])
async def generate_plan(
    request: GeneratePlanRequest,
    runtime: AppRuntime = Depends(get_runtime),
) -> APIResponse[WorkoutPlan]:
    """Run end-to-end plan generation pipeline."""

    result = await runtime.workout_planner_service.generate_plan(request)
    request_id = result.request_id or str(uuid4())

    if result.plan is None:
        error_message = "Plan generation failed"
        if result.errors:
            error_message = "; ".join(error.message for error in result.errors)
        return JSONResponse(
            status_code=500,
            content=APIResponse[WorkoutPlan](
                success=False,
                data=None,
                error=error_message,
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    return APIResponse[WorkoutPlan](
        success=True,
        data=result.plan,
        error=None,
        request_id=request_id,
    )


@router.get("/{plan_id}", response_model=APIResponse[WorkoutPlan])
async def get_plan(
    plan_id: str,
    runtime: AppRuntime = Depends(get_runtime),
) -> APIResponse[WorkoutPlan]:
    """Fetch one generated plan by plan_id."""

    plan_payload = await runtime.workout_plan_repository.get_plan(plan_id)
    request_id = str(uuid4())

    if plan_payload is None:
        return JSONResponse(
            status_code=404,
            content=APIResponse[WorkoutPlan](
                success=False,
                data=None,
                error="Plan not found",
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    plan = WorkoutPlan.model_validate(plan_payload)
    return APIResponse[WorkoutPlan](success=True, data=plan, error=None, request_id=request_id)


@users_router.get("/{user_id}/plans", response_model=APIResponse[list[UserPlanSummary]])
async def list_user_plans(
    user_id: str,
    runtime: AppRuntime = Depends(get_runtime),
) -> APIResponse[list[UserPlanSummary]]:
    """List summaries of plans for a user ordered by newest first."""

    summaries = await runtime.workout_plan_repository.list_plan_summaries_for_user(user_id)
    data = [UserPlanSummary.model_validate(item) for item in summaries]
    return APIResponse[list[UserPlanSummary]](
        success=True,
        data=data,
        error=None,
        request_id=str(uuid4()),
    )


@sessions_router.get("/{request_id}/events", response_model=APIResponse[list[SessionEvent]])
async def list_session_events(
    request_id: str,
    runtime: AppRuntime = Depends(get_runtime),
) -> APIResponse[list[SessionEvent]]:
    """List agent orchestration events for frontend progress polling."""

    events = await runtime.session_log_repository.list_events(request_id)
    data = [SessionEvent.model_validate(event) for event in events]
    return APIResponse[list[SessionEvent]](
        success=True,
        data=data,
        error=None,
        request_id=str(uuid4()),
    )


@sessions_router.get("/{request_id}/events/stream")
async def stream_session_events(
    request_id: str,
    runtime: AppRuntime = Depends(get_runtime),
) -> StreamingResponse:
    """Stream orchestration events as server-sent events for live progress UI."""

    async def event_stream() -> AsyncIterator[str]:
        seen: set[str] = set()
        idle_ticks = 0
        max_idle_ticks = 2400

        while idle_ticks < max_idle_ticks:
            emitted = False
            events = await runtime.session_log_repository.list_events(request_id)
            for event in events:
                session_event = SessionEvent.model_validate(event)
                payload = session_event.model_dump(mode="json")
                event_key = json.dumps(payload, sort_keys=True)
                if event_key in seen:
                    continue

                seen.add(event_key)
                emitted = True
                yield f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"

                if session_event.agent == "plan_export" and session_event.event == "completed":
                    yield "event: done\ndata: {}\n\n"
                    return

            idle_ticks = 0 if emitted else idle_ticks + 1
            await asyncio.sleep(0.25)

        yield "event: timeout\ndata: {}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{plan_id}/feedback", response_model=APIResponse[PlanFeedbackResponse])
async def add_plan_feedback(
    plan_id: str,
    request: PlanFeedbackRequest,
    runtime: AppRuntime = Depends(get_runtime),
) -> APIResponse[PlanFeedbackResponse]:
    """Save one feedback entry for a generated plan."""

    plan_payload = await runtime.workout_plan_repository.get_plan(plan_id)
    request_id = str(uuid4())
    if plan_payload is None:
        return JSONResponse(
            status_code=404,
            content=APIResponse[PlanFeedbackResponse](
                success=False,
                data=None,
                error="Plan not found",
                request_id=request_id,
            ).model_dump(mode="json"),
        )

    user_id = str(plan_payload.get("user_id") or "unknown")
    log_id = await runtime.session_log_repository.save_feedback(
        plan_id=plan_id,
        user_id=user_id,
        session_number=request.session_number,
        completed=request.completed,
        perceived_difficulty=request.perceived_difficulty,
        notes=request.notes,
    )

    return APIResponse[PlanFeedbackResponse](
        success=True,
        data=PlanFeedbackResponse(log_id=log_id),
        error=None,
        request_id=request_id,
    )


@constraints_router.get("/catalog", response_model=APIResponse[list[ConstraintCatalogItem]])
async def list_constraints_catalog(
    runtime: AppRuntime = Depends(get_runtime),
) -> APIResponse[list[ConstraintCatalogItem]]:
    """List medical constraint catalog entries for inspection and demos."""

    items = await runtime.medical_constraint_repository.list_constraints(limit=200)
    data: list[ConstraintCatalogItem] = []
    for item in items:
        constraint = MedicalConstraint.model_validate(item)
        data.append(
            ConstraintCatalogItem(
                condition_id=constraint.condition_id,
                canonical_name=constraint.canonical_name,
                condition_type=constraint.condition_type,
                risk_level=constraint.risk_level,
                evidence_level=constraint.evidence_level,
                affected_body_parts=constraint.affected_body_parts,
                movement_restrictions=constraint.movement_restrictions,
                safe_alternatives=constraint.safe_alternatives,
                sources=constraint.sources,
            )
        )
    return APIResponse[list[ConstraintCatalogItem]](
        success=True,
        data=data,
        error=None,
        request_id=str(uuid4()),
    )


@constraints_router.get("/search", response_model=APIResponse[ConstraintSearchResponse])
async def search_constraints(
    q: str,
    runtime: AppRuntime = Depends(get_runtime),
) -> APIResponse[ConstraintSearchResponse]:
    """Search medical constraints by canonical names or aliases."""

    items = await runtime.medical_constraint_repository.find_by_aliases_or_names([q])
    constraints = [MedicalConstraint.model_validate(item) for item in items]
    return APIResponse[ConstraintSearchResponse](
        success=True,
        data=ConstraintSearchResponse(items=constraints),
        error=None,
        request_id=str(uuid4()),
    )
