"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings for the workout-agent service."""

    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="workout_agent", alias="MONGODB_DB_NAME")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_dev_model: str = Field(default="qwen2.5:9b", alias="OLLAMA_DEV_MODEL")
    ollama_eval_model: str = Field(default="qwen2.5:35b", alias="OLLAMA_EVAL_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBEDDING_MODEL")
    ollama_timeout_seconds: float = Field(default=60.0, alias="OLLAMA_TIMEOUT_SECONDS")

    api_env: str = Field(default="development", alias="API_ENV")
    use_vector_search: bool = Field(default=False, alias="USE_VECTOR_SEARCH")
    max_risk_retries: int = Field(default=2, alias="MAX_RISK_RETRIES")
    exercise_vector_index_name: str = Field(
        default="exercise_embedding_index",
        alias="MONGODB_EXERCISE_VECTOR_INDEX",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
