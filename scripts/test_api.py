"""API integration smoke script for local server."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx


BASE_URL = "http://localhost:8000"


def _print_response(step: str, response: httpx.Response) -> dict[str, Any]:
    body = response.json()
    print(f"\n[{step}] {response.request.method} {response.request.url}")
    print(f"Status: {response.status_code}")
    print("Body:")
    print(json.dumps(body, indent=2, default=str))
    return body


def _assert_success(step: str, response_body: dict[str, Any]) -> None:
    assert response_body.get("success") is True, (
        f"{step} failed: success was not true. Body={response_body}"
    )


def _generate_payload() -> dict[str, Any]:
    return {
        "user_profile": {
            "user_id": "test-001",
            "goals": ["build muscle", "lose fat"],
            "metrics": {
                "age": 25,
                "weight_kg": 80,
                "height_cm": 180,
                "sex": "male",
            },
            "availability": {
                "days_per_week": 4,
                "minutes_per_session": 60,
                "preferred_days": [],
            },
            "equipment": ["barbell", "dumbbells", "rack"],
            "experience_level": "intermediate",
            "notes": None,
        },
        "constraints": {
            "injuries": ["left_knee_pain"],
            "chronic_conditions": [],
            "restrictions": [],
            "contraindications": [],
        },
        "weeks": 4,
        "use_eval_model": False,
    }


async def main() -> None:
    timeout = httpx.Timeout(timeout=300.0)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=timeout) as client:
        health_response = await client.get("/health")
        health_body = _print_response("1", health_response)
        _assert_success("GET /health", health_body)

        generate_response = await client.post("/v1/plans/generate", json=_generate_payload())
        generate_body = _print_response("2", generate_response)
        _assert_success("POST /v1/plans/generate", generate_body)

        plan_id = generate_body["data"]["plan_id"]

        get_plan_response = await client.get(f"/v1/plans/{plan_id}")
        get_plan_body = _print_response("3", get_plan_response)
        _assert_success("GET /v1/plans/{plan_id}", get_plan_body)

        list_response = await client.get("/v1/users/test-001/plans")
        list_body = _print_response("4", list_response)
        _assert_success("GET /v1/users/test-001/plans", list_body)

        feedback_payload = {
            "session_number": 1,
            "completed": True,
            "perceived_difficulty": 3,
            "notes": "Felt manageable and knee was stable.",
        }
        feedback_response = await client.post(
            f"/v1/plans/{plan_id}/feedback",
            json=feedback_payload,
        )
        feedback_body = _print_response("5", feedback_response)
        _assert_success("POST /v1/plans/{plan_id}/feedback", feedback_body)

    print("\nALL API TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
