"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from workout_agent.api.routes import constraints_router, sessions_router, users_router
from workout_agent.api.routes import router as plans_router
from workout_agent.api.schemas import APIResponse, HealthResponse
from workout_agent.services.runtime import AppRuntime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and teardown runtime resources."""

    runtime = AppRuntime()
    app.state.runtime = runtime
    await runtime.startup()
    try:
        yield
    finally:
        await runtime.shutdown()


app = FastAPI(
    title="Workout Agent API",
    description="Multi-agent workout schedule generation service",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(plans_router)
app.include_router(users_router)
app.include_router(constraints_router)
app.include_router(sessions_router)


@app.exception_handler(ValueError)
async def handle_value_error(_: Request, exc: ValueError) -> JSONResponse:
    payload = APIResponse[dict](success=False, data=None, error=str(exc), request_id=str(uuid4()))
    return JSONResponse(status_code=400, content=payload.model_dump(mode="json"))


@app.exception_handler(KeyError)
async def handle_key_error(_: Request, exc: KeyError) -> JSONResponse:
    payload = APIResponse[dict](success=False, data=None, error=str(exc), request_id=str(uuid4()))
    return JSONResponse(status_code=400, content=payload.model_dump(mode="json"))


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    payload = APIResponse[dict](success=False, data=None, error=str(exc), request_id=str(uuid4()))
    return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))


@app.get("/health", tags=["system"], response_model=APIResponse[HealthResponse])
async def health(request: Request) -> APIResponse[HealthResponse]:
    """Health endpoint for runtime checks."""

    runtime: AppRuntime = request.app.state.runtime
    health_status = await runtime.health()
    return APIResponse[HealthResponse](
        success=True,
        data=HealthResponse(status=health_status.status, mongodb=health_status.mongodb),
        error=None,
        request_id=str(uuid4()),
    )
