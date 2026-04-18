"""Runtime container for infrastructure and service wiring."""

from __future__ import annotations

from dataclasses import dataclass

from workout_agent.core.config import Settings, get_settings
from workout_agent.core.state import RuntimeDependencies
from workout_agent.db.mongo import MongoConnection
from workout_agent.db.repositories import (
    ExerciseRepository,
    SessionLogRepository,
    UserRepository,
    WorkoutPlanRepository,
)
from workout_agent.services.ollama_client import OllamaClient
from workout_agent.services.planner_service import WorkoutPlannerService
from workout_agent.services.workout_graph import build_workout_graph


@dataclass
class HealthStatus:
    """Health snapshot for readiness/liveness endpoints."""

    status: str
    mongodb: str


class AppRuntime:
    """Application runtime with initialized clients, repositories, and services."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

        self.mongo = MongoConnection(
            uri=self.settings.mongodb_uri, db_name=self.settings.mongodb_db_name
        )
        self.ollama_client = OllamaClient(
            base_url=self.settings.ollama_base_url,
            timeout_seconds=self.settings.ollama_timeout_seconds,
        )

        self.exercise_repository = ExerciseRepository(
            self.mongo.collection("exercises"),
            vector_index_name=self.settings.exercise_vector_index_name,
        )
        self.workout_plan_repository = WorkoutPlanRepository(self.mongo.collection("workout_plans"))
        self.user_repository = UserRepository(self.mongo.collection("users"))
        self.session_log_repository = SessionLogRepository(self.mongo.collection("session_logs"))

        self.graph = build_workout_graph()
        self.workout_planner_service = WorkoutPlannerService(
            graph=self.graph,
            runtime_dependencies=self.runtime_dependencies,
        )

    @property
    def runtime_dependencies(self) -> RuntimeDependencies:
        """Dependencies dictionary injected into the agent state."""

        return RuntimeDependencies(
            settings=self.settings,
            ollama_client=self.ollama_client,
            exercise_repository=self.exercise_repository,
            workout_plan_repository=self.workout_plan_repository,
            user_repository=self.user_repository,
            session_log_repository=self.session_log_repository,
        )

    async def startup(self) -> None:
        """Run startup checks."""

        await self.mongo.ping()

    async def shutdown(self) -> None:
        """Gracefully close runtime resources."""

        await self.ollama_client.aclose()
        self.mongo.close()

    async def health(self) -> HealthStatus:
        """Return current runtime health status."""

        try:
            await self.mongo.ping()
            return HealthStatus(status="ok", mongodb="ok")
        except Exception:
            return HealthStatus(status="degraded", mongodb="unreachable")
