from __future__ import annotations

import os
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _HAS_PYDANTIC_SETTINGS = True
except Exception:  # pragma: no cover - exercised in local fallback validation
    from pydantic import BaseModel

    BaseSettings = BaseModel  # type: ignore[assignment]
    _HAS_PYDANTIC_SETTINGS = False

    def SettingsConfigDict(**kwargs):  # type: ignore[no-redef]
        return kwargs


class Settings(BaseSettings):
    if _HAS_PYDANTIC_SETTINGS:
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "service"
    log_level: str = "INFO"

    environment: str = "dev"
    service_token: str = ""

    database_url: str = "postgresql://copilot:copilot@timescaledb:5432/copilot"

    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "documents"

    minio_endpoint: str = "http://minio:9000"
    minio_access_key: str = "minio"
    minio_secret_key: str = "minio123"
    minio_bucket: str = "raw-docs"

    audit_service_url: str = "http://audit-log:8009"

    gateway_port: int = 8001
    orchestrator_url: str = "http://orchestrator:8002"
    memory_service_url: str = "http://memory-retrieval:8007"
    parser_service_url: str = "http://parser-normalizer:8006"
    risk_service_url: str = "http://risk-stub:8008"

    exchange_id: str = "binance"
    exchange_symbols: str = "BTC/USDT,SOL/USDT,ETH/USDT"
    market_rest_poll_seconds: float = 10.0
    market_ws_enabled: bool = True

    news_rss_urls: str = (
        "https://www.coindesk.com/arc/outboundfeeds/rss/,"
        "https://cointelegraph.com/rss"
    )
    news_poll_seconds: float = 180.0

    archive_max_snapshots: int = 3

    request_timeout_seconds: float = 15.0

    no_trading: bool = True

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_reasoning_model: str = "o4-mini"
    openai_base_url: str = ""

    @property
    def exchange_symbols_list(self) -> list[str]:
        return [s.strip() for s in self.exchange_symbols.split(",") if s.strip()]

    @property
    def news_rss_list(self) -> list[str]:
        return [u.strip() for u in self.news_rss_urls.split(",") if u.strip()]


def _fallback_env_values() -> dict[str, str]:
    return {
        field_name: raw_value
        for field_name in Settings.model_fields
        if (raw_value := os.environ.get(field_name.upper())) is not None
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    if _HAS_PYDANTIC_SETTINGS:
        return Settings()
    return Settings(**_fallback_env_values())
