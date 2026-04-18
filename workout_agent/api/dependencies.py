"""FastAPI dependency providers."""

from __future__ import annotations

from fastapi import Request

from workout_agent.services.runtime import AppRuntime


def get_runtime(request: Request) -> AppRuntime:
    """Return initialized application runtime from app state."""

    return request.app.state.runtime
