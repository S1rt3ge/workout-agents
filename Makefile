install:
	poetry install

seed:
	poetry run python scripts/seed_exercises.py

smoke:
	poetry run python scripts/smoke_test.py

dev:
	poetry run uvicorn workout_agent.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-up-llm:
	docker compose -f docker-compose.yml -f docker-compose.llm.yml up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f backend

docker-seed:
	docker compose exec backend poetry run python scripts/seed_exercises.py
