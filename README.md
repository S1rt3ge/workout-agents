# Workout Agent

Production-focused multi-agent workout planning platform that generates personalized training programs from user goals, body metrics, equipment availability, and safety constraints.

The system combines a LangGraph-based orchestration pipeline, local LLM inference via Ollama, a FastAPI backend, MongoDB persistence, and a Next.js frontend for onboarding, plan review, and feedback tracking.

## Executive Summary

`Workout Agent` is an applied AI systems project focused on a realistic product problem: generating personalized workout plans without relying on a single monolithic prompt.

Instead of treating plan generation as one-shot text generation, the system breaks the workflow into specialized agent stages with typed state, explicit safety review, deterministic post-processing, persistence, and a user-facing web application.

In practice, this project demonstrates:
- multi-agent orchestration with LangGraph
- local LLM integration through Ollama
- schema-first backend design with FastAPI and Pydantic v2
- MongoDB-backed storage for plans, exercises, and feedback
- full-stack delivery with a typed Next.js frontend
- repeatable verification through smoke and end-to-end API checks

## Why This Project Is Interesting

- It mixes probabilistic LLM reasoning with deterministic safeguards where correctness matters.
- It treats safety as part of system design, not as a cosmetic afterthought.
- It includes both backend architecture and frontend product delivery.
- It is structured like a real application, not just an experiment notebook or prompt demo.

## Overview

`workout-agent` is built around a practical idea: workout generation should not be handled by a single prompt. Instead, the planning workflow is decomposed into specialized stages that each solve one part of the problem: intake, safety interpretation, exercise selection, scheduling, progression, risk review, explainability, and export.

This repository contains:
- A Python backend with an 8-agent LangGraph pipeline
- A MongoDB-backed persistence layer for users, plans, exercises, and feedback logs
- A local LLM integration through Ollama and Qwen2.5 models
- A typed REST API built with FastAPI
- A Next.js frontend for onboarding, generation flow, dashboard, and plan detail pages
- Containerization assets for local multi-service deployment

## Core Capabilities

- Personalized plan generation from user profile and training constraints
- Shared typed orchestration state across specialized agents
- Hard safety review stage before plan export
- Explainable output for key planning decisions
- Plan persistence and retrieval via REST API
- Session feedback logging for future adaptation workflows
- Frontend onboarding and plan review flow connected to the backend API

## Architecture

The backend uses a staged agent pipeline orchestrated with LangGraph `StateGraph`.

### Architecture Diagram

```text
                        +----------------------+
                        |   Next.js Frontend   |
                        | onboarding/dashboard |
                        +----------+-----------+
                                   |
                                   | HTTP
                                   v
                     +-------------+-------------+
                     |       FastAPI Backend     |
                     |  typed API + app runtime  |
                     +-------------+-------------+
                                   |
                                   v
                     +-------------+-------------+
                     |      LangGraph Pipeline   |
                     |      shared AgentState    |
                     +-------------+-------------+
                                   |
      ----------------------------------------------------------------------
      |            |              |              |             |             |
      v            v              v              v             v             v
 +---------+  +-----------+  +-----------+  +-----------+  +-----------+  +-----------+
 | intake  |->| constraints|->| exercise  |->| schedule  |->| progress  |->|   risk    |
 | agent   |  |   agent    |  | selector  |  |  maker    |  | planner   |  | assessment|
 +---------+  +-----------+  +-----------+  +-----------+  +-----------+  +-----------+
                                                                                  |
                                                                                  | loop on critical issues
                                                                                  v
                                                                            +-----------+
                                                                            | selector  |
                                                                            +-----------+
                                                                                  |
                                                                                  v
                                                                            +-----------+
                                                                            | explain-  |
                                                                            | ability   |
                                                                            +-----------+
                                                                                  |
                                                                                  v
                                                                            +-----------+
                                                                            | plan      |
                                                                            | export    |
                                                                            +-----------+

                     External services:
                     - Ollama for local LLM inference
                     - MongoDB for exercises, users, plans, session logs
```

### Agent Pipeline

1. `information_receiver`
2. `constraint_receiver`
3. `exercise_selector`
4. `schedule_maker`
5. `progress_planner`
6. `risk_assessment`
7. `explainability`
8. `plan_export`

### Orchestration Model

- All agents receive and return a shared `AgentState`
- Each agent is an isolated async module with `async def run(state: AgentState) -> AgentState`
- `risk_assessment` can force a loop back to `exercise_selector` when critical issues are detected
- Errors are accumulated into `state.errors` rather than being silently swallowed
- Runtime services are injected into state rather than accessed globally

### Safety Model

Safety is treated as a first-class concern rather than a post-processing note.

- User injuries, conditions, and restrictions are normalized into contraindications
- Candidate exercises are filtered against equipment and constraint data
- Risk review operates as a dedicated pipeline stage
- The scheduling layer applies deterministic routing rules to reduce category leakage across training days

## Tech Stack

### Backend

- Python 3.11
- FastAPI
- Uvicorn
- LangGraph
- Ollama
- Qwen2.5 local models
- MongoDB
- Motor
- Pydantic v2
- Poetry

### Frontend

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- React Three Fiber
- Zustand

### Tooling

- Pytest
- Ruff
- MyPy
- Docker
- Docker Compose

## Repository Layout

```text
.
├── workout_agent/              # Python backend package
│   ├── agents/                 # 8 specialized pipeline agents
│   ├── api/                    # FastAPI routes, schemas, dependencies
│   ├── core/                   # settings and shared state
│   ├── db/                     # Mongo connection and repositories
│   ├── models/                 # Pydantic domain and API models
│   └── services/               # graph, runtime, planner, Ollama client
├── scripts/                    # seed, smoke, API and graph verification scripts
├── b_sCMmptobhu2/              # Next.js frontend application
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── Makefile
```

## Backend Design Notes

### Typed State and Models

The backend uses strongly typed Pydantic models and a shared `TypedDict` orchestration state.

Important model families include:
- user profile and availability models
- exercise and prescription models
- weekly schedule and progression models
- safety assessment and explainability models
- API response wrappers and feedback payloads

### API Design

All HTTP endpoints return a standard typed wrapper:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "..."
}
```

This keeps client handling consistent across success and failure paths.

### Persistence

MongoDB collections currently support:
- `users`
- `workout_plans`
- `session_logs`
- `exercises`

The exercise collection acts as the knowledge base for retrieval-driven selection.

## Frontend Overview

The frontend is designed as a product-facing experience rather than a demo shell.

Implemented flows include:
- marketing landing page
- onboarding flow for user plan generation
- generation screen with agent-processing visualization
- dashboard for previously generated plans
- plan detail page with session feedback submission

The frontend consumes the FastAPI API through a typed client layer and stores active plan state in Zustand.

## REST API

### Health

- `GET /health`

Returns runtime health status wrapped in the shared API envelope.

### Plans

- `POST /v1/plans/generate`
- `GET /v1/plans/{plan_id}`
- `GET /v1/users/{user_id}/plans`
- `POST /v1/plans/{plan_id}/feedback`

### Example Request

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

## Local Development

### Prerequisites

- Python 3.11
- Poetry
- Node.js + npm
- MongoDB available on `localhost:27017`
- Ollama available on `localhost:11434`
- Local Qwen2.5 models pulled in Ollama

### Backend Setup

```bash
poetry install
```

Copy environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Seed the exercise collection:

```bash
make seed
```

Run the backend:

```bash
make dev
```

### Frontend Setup

```bash
cd b_sCMmptobhu2
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Frontend default URL:

- `http://localhost:3000`

Backend default URL:

- `http://localhost:8000`

## Verification Scripts

The repository includes executable verification helpers.

### Smoke Test

Validates imports and state schema without requiring live external services.

```bash
python scripts/smoke_test.py
```

Expected output:

```text
ALL IMPORTS OK
STATE SCHEMA OK
```

### Graph Direct Run

Runs the full LangGraph workflow directly, bypassing HTTP, using a hardcoded test profile.

```bash
poetry run python scripts/run_graph_direct.py
```

Useful for:
- checking agent-by-agent execution
- inspecting final plan structure
- validating `state.errors[]`

### API Integration Check

Runs an end-to-end backend API flow:
- health
- generate plan
- fetch generated plan
- list user plans
- submit feedback

```bash
python scripts/e2e_check.py
```

Current verified output:

```text
5/5 checks passed
```

## Docker

### Build Backend Image

```bash
docker build -t workout-agent-backend .
```

### Run Full Stack with Compose

```bash
docker compose up --build
```

Compose services:
- `backend`
- `mongo`
- `ollama`

Persistent named volumes:
- `mongo_data`
- `ollama_data`

## Engineering Highlights

- Asynchronous backend architecture end-to-end
- Typed API contracts on both backend and frontend
- Multi-agent orchestration with explicit state transitions
- Retrieval-aware exercise selection against stored exercise documents
- Dedicated safety review stage with loopback support
- Deterministic post-processing where LLM-only routing proved unreliable
- End-to-end API verification script for repeatable regression checks

## Resume-Oriented Highlights

If this repository is being reviewed as portfolio work, the most relevant engineering signals are:

- Designed and implemented a multi-stage LLM workflow instead of relying on a single prompt chain
- Built a typed, async FastAPI backend with explicit runtime wiring and structured error handling
- Integrated local-model inference via Ollama into a production-style service boundary
- Used deterministic rule enforcement to correct failure modes where LLM outputs were not reliable enough
- Delivered full-stack functionality, including API integration, onboarding UX, dashboard views, and feedback submission
- Added practical operational tooling: smoke tests, end-to-end checks, Docker image, and Compose stack

## What This Project Demonstrates

This project is a good representation of practical applied AI engineering rather than prompt-only prototyping.

It demonstrates:
- decomposition of a complex LLM workflow into specialized agents
- disciplined schema-first design around LLM outputs
- integration of local inference runtimes into production-style services
- mixing probabilistic reasoning with deterministic guards
- full-stack delivery across backend, frontend, persistence, and containerization

## Limitations and Future Work

Current limitations:
- local-model inference time is still significant for full plan generation
- exercise routing quality is improved, but still an area for continued refinement
- feedback currently stores session logs, but adaptive re-planning is only partially implemented
- deployment orchestration is prepared at the container level, but not yet production hosted

Potential next steps:
- pre-computed exercise embeddings and stronger retrieval ranking
- richer plan validation and scheduling heuristics
- auth and user identity management
- background jobs for long-running generation requests
- hosted deployment with externalized persistence and model runtime strategy

## License

No license file is currently included in this repository.
