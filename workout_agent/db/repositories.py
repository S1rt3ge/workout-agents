"""Repository implementations for MongoDB collections."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import TypeAdapter

from workout_agent.models.domain import Exercise, MedicalConstraint, WorkoutPlan


def _normalize_search_term(value: str) -> str:
    """Normalize free-text condition terms for lookups."""

    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9\s]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


class ExerciseRepository:
    """Read access to exercise knowledge base with vector search."""

    def __init__(self, collection: Any, vector_index_name: str) -> None:
        self._collection = collection
        self._vector_index_name = vector_index_name
        self._exercise_list_adapter = TypeAdapter(list[Exercise])

    async def vector_search(
        self,
        *,
        embedding: list[float],
        limit: int = 24,
        filters: dict[str, Any] | None = None,
    ) -> list[Exercise]:
        """Search exercise documents by embedding similarity."""

        pipeline: list[dict[str, Any]] = [
            {
                "$vectorSearch": {
                    "index": self._vector_index_name,
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": max(limit * 5, 50),
                    "limit": limit,
                    "filter": filters or {},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "exercise_id": {"$ifNull": ["$exercise_id", {"$toString": "$_id"}]},
                    "name": 1,
                    "primary_muscles": {
                        "$ifNull": ["$primary_muscles", {"$ifNull": ["$muscle_groups", []]}]
                    },
                    "secondary_muscles": {"$ifNull": ["$secondary_muscles", []]},
                    "equipment": {"$ifNull": ["$equipment", []]},
                    "contraindications": {"$ifNull": ["$contraindications", []]},
                    "difficulty": 1,
                    "instructions": 1,
                    "category": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        docs = [doc async for doc in self._collection.aggregate(pipeline)]
        return self._exercise_list_adapter.validate_python(docs)

    async def list_exercises(
        self,
        *,
        limit: int = 24,
        filters: dict[str, Any] | None = None,
    ) -> list[Exercise]:
        """Fallback listing for exercises when vector search is unavailable."""

        query = filters or {}
        projection = {
            "_id": 0,
            "exercise_id": 1,
            "name": 1,
            "primary_muscles": 1,
            "muscle_groups": 1,
            "secondary_muscles": 1,
            "equipment": 1,
            "contraindications": 1,
            "difficulty": 1,
            "instructions": 1,
            "category": 1,
        }

        docs = [doc async for doc in self._collection.find(query, projection).limit(limit)]
        for doc in docs:
            if not doc.get("exercise_id"):
                doc["exercise_id"] = doc.get("name", "unknown_exercise").lower().replace(" ", "_")
            if not doc.get("primary_muscles") and doc.get("muscle_groups"):
                doc["primary_muscles"] = doc.get("muscle_groups", [])
        return self._exercise_list_adapter.validate_python(docs)


class MedicalConstraintRepository:
    """Read access to the structured medical constraints knowledge base."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection
        self._constraint_list_adapter = TypeAdapter(list[MedicalConstraint])

    async def find_by_aliases_or_names(self, terms: list[str]) -> list[dict[str, Any]]:
        """Find constraints matching normalized aliases or canonical names."""

        normalized_terms = unique_terms = [
            term for term in (_normalize_search_term(value) for value in terms) if term
        ]
        if not normalized_terms:
            return []

        seen: set[str] = set()
        deduplicated_terms: list[str] = []
        for term in unique_terms:
            if term in seen:
                continue
            seen.add(term)
            deduplicated_terms.append(term)

        query = {
            "$or": [
                {"search_terms": {"$in": deduplicated_terms}},
                {
                    "canonical_name": {
                        "$in": [
                            re.compile(f"^{re.escape(term)}$", re.IGNORECASE)
                            for term in deduplicated_terms
                        ]
                    }
                },
                {
                    "aliases": {
                        "$in": [
                            re.compile(f"^{re.escape(term)}$", re.IGNORECASE)
                            for term in deduplicated_terms
                        ]
                    }
                },
            ]
        }
        docs = [doc async for doc in self._collection.find(query, {"_id": 0})]
        constraints = self._constraint_list_adapter.validate_python(docs)
        return [constraint.model_dump(mode="python") for constraint in constraints]

    async def find_by_condition_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Fetch constraints by stable condition identifiers."""

        normalized_ids = [value.strip() for value in ids if value.strip()]
        if not normalized_ids:
            return []

        docs = [
            doc
            async for doc in self._collection.find(
                {"condition_id": {"$in": normalized_ids}},
                {"_id": 0},
            )
        ]
        constraints = self._constraint_list_adapter.validate_python(docs)
        return [constraint.model_dump(mode="python") for constraint in constraints]

    async def list_constraints(self, limit: int = 100) -> list[dict[str, Any]]:
        """List constraints ordered by canonical name."""

        docs = [
            doc
            async for doc in self._collection.find({}, {"_id": 0})
            .sort("canonical_name", 1)
            .limit(limit)
        ]
        constraints = self._constraint_list_adapter.validate_python(docs)
        return [constraint.model_dump(mode="python") for constraint in constraints]

class WorkoutPlanRepository:
    """Persistence for generated workout plans."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def save_plan(self, plan: WorkoutPlan) -> str:
        """Upsert workout plan by plan_id."""

        now = datetime.now(UTC)
        payload = plan.model_dump(mode="python")
        created_at = payload.pop("created_at", now)
        payload["updated_at"] = now

        await self._collection.update_one(
            {"plan_id": plan.plan_id},
            {"$set": payload, "$setOnInsert": {"created_at": created_at}},
            upsert=True,
        )
        return plan.plan_id

    async def get_plan(self, plan_id: str) -> dict[str, Any] | None:
        """Fetch one plan by id."""

        return await self._collection.find_one({"plan_id": plan_id}, {"_id": 0, "updated_at": 0})

    async def list_plan_summaries_for_user(self, user_id: str) -> list[dict[str, Any]]:
        """List lightweight plan summaries for a given user."""

        pipeline: list[dict[str, Any]] = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"created_at": -1}},
            {
                "$project": {
                    "_id": 0,
                    "plan_id": 1,
                    "status": 1,
                    "created_at": 1,
                    "week_number": {"$ifNull": ["$weeks", 1]},
                }
            },
        ]
        return [doc async for doc in self._collection.aggregate(pipeline)]


class UserRepository:
    """Persistence for user profile snapshots."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def upsert_user_profile(self, user_id: str, profile_payload: dict[str, Any]) -> None:
        """Upsert user profile by user_id."""

        await self._collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "profile": profile_payload,
                    "updated_at": datetime.now(UTC),
                }
            },
            upsert=True,
        )


class SessionLogRepository:
    """Write-only repository for orchestration session events."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def log_event(
        self,
        *,
        request_id: str,
        agent: str,
        event: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Insert a session event row."""

        await self._collection.insert_one(
            {
                "request_id": request_id,
                "agent": agent,
                "event": event,
                "payload": payload or {},
                "timestamp": datetime.now(UTC),
            }
        )

    async def list_events(self, request_id: str) -> list[dict[str, Any]]:
        """Return orchestration events for one request ordered by insertion time."""

        return [
            doc
            async for doc in self._collection.find(
                {"request_id": request_id},
                {"_id": 0},
            ).sort("timestamp", 1)
        ]

    async def save_feedback(
        self,
        *,
        plan_id: str,
        user_id: str,
        session_number: int,
        completed: bool,
        perceived_difficulty: int,
        notes: str | None,
    ) -> str:
        """Persist user session feedback and return generated log identifier."""

        log_id = str(uuid4())
        await self._collection.insert_one(
            {
                "log_id": log_id,
                "event_type": "plan_feedback",
                "plan_id": plan_id,
                "user_id": user_id,
                "session_number": session_number,
                "completed": completed,
                "perceived_difficulty": perceived_difficulty,
                "notes": notes,
                "timestamp": datetime.now(UTC),
            }
        )
        return log_id
