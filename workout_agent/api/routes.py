"""API routes for workout plan generation."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from workout_agent.api.dependencies import get_runtime
from workout_agent.api.schemas import (
    APIResponse,
    PlanFeedbackRequest,
    PlanFeedbackResponse,
    UserPlanSummary,
)
from workout_agent.models.api import GeneratePlanRequest
from workout_agent.models.domain import WorkoutPlan
from workout_agent.services.runtime import AppRuntime

router = APIRouter(prefix="/v1/plans", tags=["plans"])
users_router = APIRouter(prefix="/v1/users", tags=["users"])


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
