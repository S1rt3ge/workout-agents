FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry --no-cache-dir

COPY pyproject.toml poetry.lock README.md ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

COPY workout_agent ./workout_agent
COPY scripts ./scripts

EXPOSE 8000
CMD ["uvicorn", "workout_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
