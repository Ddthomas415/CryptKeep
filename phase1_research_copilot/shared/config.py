from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "service"
    log_level: str = "INFO"

    environment: str = "dev"

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

    @property
    def exchange_symbols_list(self) -> list[str]:
        return [s.strip() for s in self.exchange_symbols.split(",") if s.strip()]

    @property
    def news_rss_list(self) -> list[str]:
        return [u.strip() for u in self.news_rss_urls.split(",") if u.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
