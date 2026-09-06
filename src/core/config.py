"""Application configuration, loaded from environment / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Anthropic
    anthropic_api_key: str = ""
    model: str = "claude-opus-5"

    # Agent behaviour
    max_agent_steps: int = 6
    agent_max_tokens: int = 4096

    # Storage
    database_path: str = "support.db"
    seed_on_startup: bool = True

    @property
    def llm_configured(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
