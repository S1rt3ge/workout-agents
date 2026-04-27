"""End-to-end API flow verification script."""

from __future__ import annotations

import time
from typing import Any

import httpx

BASE_URL = "http://localhost:8000"


def print_result(step: str, passed: bool, elapsed_ms: float, details: str = "") -> None:
    status = "PASS" if passed else "FAIL"
    message = f"[{status}] {step} ({elapsed_ms:.1f} ms)"
    if details:
        message += f" - {details}"
    print(message)


def run() -> int:
    checks_passed = 0
    total_checks = 5
    plan_id: str | None = None

    payload = {
        "user_profile": {
            "user_id": "e2e-test-001",
            "goals": ["build muscle"],
            "metrics": {
                "age": 26,
                "weight_kg": 78,
                "height_cm": 178,
                "sex": "prefer_not_to_say",
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

    timeout = httpx.Timeout(900.0)

    with httpx.Client(base_url=BASE_URL, timeout=timeout) as client:
        # 1) health
        start = time.perf_counter()
        try:
            response = client.get("/health")
            elapsed_ms = (time.perf_counter() - start) * 1000
            body = response.json()
            passed = response.status_code == 200 and body.get("success") is True
            print_result("1) GET /health", passed, elapsed_ms)
            if passed:
                checks_passed += 1
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print_result("1) GET /health", False, elapsed_ms, str(exc))

        # 2) generate
        start = time.perf_counter()
        try:
            response = client.post("/v1/plans/generate", json=payload)
            elapsed_ms = (time.perf_counter() - start) * 1000
            body = response.json()
            passed = (
                response.status_code == 200 and body.get("success") is True and body.get("data")
            )
            if passed:
                plan_id = body["data"].get("plan_id")
            print_result(
                "2) POST /v1/plans/generate", bool(passed), elapsed_ms, f"plan_id={plan_id}"
            )
            if passed:
                checks_passed += 1
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print_result("2) POST /v1/plans/generate", False, elapsed_ms, str(exc))

        # 3) get plan
        start = time.perf_counter()
        try:
            if not plan_id:
                raise RuntimeError("plan_id missing from step 2")
            response = client.get(f"/v1/plans/{plan_id}")
            elapsed_ms = (time.perf_counter() - start) * 1000
            body = response.json()
            passed = (
                response.status_code == 200 and body.get("success") is True and body.get("data")
            )
            print_result("3) GET /v1/plans/{plan_id}", bool(passed), elapsed_ms)
            if passed:
                checks_passed += 1
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print_result("3) GET /v1/plans/{plan_id}", False, elapsed_ms, str(exc))

        # 4) list user plans
        start = time.perf_counter()
        try:
            response = client.get("/v1/users/e2e-test-001/plans")
            elapsed_ms = (time.perf_counter() - start) * 1000
            body = response.json()
            plans = body.get("data") if isinstance(body, dict) else None
            passed = (
                response.status_code == 200
                and body.get("success") is True
                and isinstance(plans, list)
            )
            print_result(
                "4) GET /v1/users/e2e-test-001/plans",
                bool(passed),
                elapsed_ms,
                f"count={len(plans) if isinstance(plans, list) else 0}",
            )
            if passed:
                checks_passed += 1
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print_result("4) GET /v1/users/e2e-test-001/plans", False, elapsed_ms, str(exc))

        # 5) submit feedback
        start = time.perf_counter()
        try:
            if not plan_id:
                raise RuntimeError("plan_id missing from step 2")
            feedback_payload: dict[str, Any] = {
                "session_number": 1,
                "completed": True,
                "perceived_difficulty": 3,
                "notes": "felt good",
            }
            response = client.post(f"/v1/plans/{plan_id}/feedback", json=feedback_payload)
            elapsed_ms = (time.perf_counter() - start) * 1000
            body = response.json()
            log_id = None
            if isinstance(body, dict) and isinstance(body.get("data"), dict):
                log_id = body["data"].get("log_id")
            passed = response.status_code == 200 and body.get("success") is True and bool(log_id)
            print_result(
                "5) POST /v1/plans/{plan_id}/feedback", bool(passed), elapsed_ms, f"log_id={log_id}"
            )
            if passed:
                checks_passed += 1
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print_result("5) POST /v1/plans/{plan_id}/feedback", False, elapsed_ms, str(exc))

    print(f"\n{checks_passed}/{total_checks} checks passed")
    return 0 if checks_passed == total_checks else 1


if __name__ == "__main__":
    raise SystemExit(run())
