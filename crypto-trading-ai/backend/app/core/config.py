from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+psycopg://app:app@postgres:5432/trading_ai"
    redis_url: str = "redis://redis:6379/0"
    vector_db_url: str = "http://vector:6333"

    openai_api_key: str = ""
    news_api_key: str = ""

    wayback_enabled: bool = True
    default_mode: str = "research_only"
    log_level: str = "INFO"
    enable_metrics: bool = True
    enable_tracing: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
