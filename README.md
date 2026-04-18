# Workout Agent

Production-ready multi-agent LLM system for generating safe and personalized workout schedules.

## Stack

- Python 3.11
- LangGraph (StateGraph)
- Ollama (Qwen2.5 models)
- FastAPI + Uvicorn
- MongoDB + Motor
- Pydantic v2
- Poetry

## Quick Start

### Prerequisites

- Python 3.11
- Poetry
- MongoDB running locally
- Ollama running locally with `qwen2.5:9b` pulled

### Run locally

1. Install dependencies:

```bash
poetry install
```

2. Copy environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

3. Seed exercise knowledge base:

```bash
make seed
```

4. Start the API in development mode:

```bash
make dev
```

5. Send a request to generate a plan:

```bash
curl -X POST "http://localhost:8000/v1/plans/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "user_id": "user-123",
      "goals": ["build muscle", "lose fat"],
      "metrics": {
        "age": 29,
        "height_cm": 178,
        "weight_kg": 82,
        "sex": "male"
      },
      "availability": {
        "days_per_week": 4,
        "minutes_per_session": 60,
        "preferred_days": ["Monday", "Tuesday", "Thursday", "Saturday"]
      },
      "equipment": ["barbell", "dumbbells", "rack"],
      "experience_level": "intermediate",
      "notes": "Prefer compound lifts first in each workout"
    },
    "constraints": {
      "injuries": ["left_knee_pain"],
      "chronic_conditions": [],
      "restrictions": ["avoid deep knee flexion under heavy load"],
      "contraindications": []
    },
    "weeks": 4,
    "use_eval_model": false
  }'
```

## API

- `POST /v1/plans/generate` — generates a workout plan from profile + constraints.
- `GET /health` — liveness endpoint.

## Architecture

The orchestrator uses an 8-agent LangGraph pipeline:

1. information_receiver
2. constraint_receiver
3. exercise_selector
4. schedule_maker
5. progress_planner
6. risk_assessment
7. explainability
8. plan_export

`risk_assessment` is a hard gate. On critical risk, execution loops back to `exercise_selector`.

## Notes

- Business logic is implemented in agent modules and services, not routes.
- Agent communication uses a shared typed state object.
- Errors are appended into `state.errors`.
