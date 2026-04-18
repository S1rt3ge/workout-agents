install:
	poetry install

seed:
	poetry run python scripts/seed_exercises.py

smoke:
	poetry run python scripts/smoke_test.py

dev:
	poetry run uvicorn workout_agent.main:app --reload --host 0.0.0.0 --port 8000
