from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        return int(value) if value not in (None, "") else int(default)
    except Exception:
        return int(default)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    try:
        return float(value) if value not in (None, "") else float(default)
    except Exception:
        return float(default)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    app_env: str = "local"
    log_level: str = "INFO"
    service_name: str = "service"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "trade_ai"
    postgres_user: str = "trade_ai"
    postgres_password: str = "trade_ai"

    redis_url: str = "redis://redis:6379/0"

    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "documents"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"

    newsapi_api_key: str = ""

    coinbase_api_key: str = ""
    coinbase_api_secret: str = ""
    coinbase_api_passphrase: str = ""
    coinbase_use_sandbox: bool = True
    live_custody_provider: str = "env"
    live_custody_key_id: str = ""
    live_custody_secret_id: str = ""
    live_custody_last_rotated_at: str = ""
    live_custody_rotation_max_age_days: int = 90

    wayback_base_url: str = "https://archive.org"
    commoncrawl_index_url: str = "https://index.commoncrawl.org"

    execution_enabled: bool = False
    paper_trading_enabled: bool = False
    live_execution_sandbox_enabled: bool = False
    live_execution_sandbox_transport_enabled: bool = False
    live_execution_provider: str = "mock"
    live_router_max_spread_bps: float = 120.0
    live_router_max_estimated_cost_bps: float = 180.0
    live_router_fee_bps_coinbase: float = 8.0
    live_router_fee_bps_binance: float = 10.0
    live_router_fee_bps_kraken: float = 16.0
    live_router_alert_min_decisions: int = 20
    live_router_alert_min_route_eligible_rate: float = 0.60
    live_router_alert_min_feasible_route_rate: float = 0.55
    live_router_alert_max_spread_blocker_ratio: float = 0.30
    live_router_alert_max_cost_blocker_ratio: float = 0.30
    live_router_retention_days: int = 90
    live_router_gate_retention_days: int = 180
    live_router_incident_retention_days: int = 180
    live_execution_submission_retention_days: int = 180
    paper_initial_usd_balance: float = 100000.0
    paper_market_slippage_bps: float = 5.0
    paper_fee_bps: float = 0.0
    paper_max_notional_usd: float = 25000.0
    paper_max_position_qty: float = 100.0
    paper_daily_loss_limit_usd: float = 2000.0
    paper_order_require_approval: bool = False
    paper_alert_drawdown_pct_threshold: float = 10.0
    paper_alert_concentration_pct_threshold: float = 60.0
    paper_min_performance_days: int = 7
    paper_min_performance_points: int = 24
    paper_retention_days: int = 180

    gateway_port: int = 8000
    orchestrator_port: int = 8001
    market_data_port: int = 8002
    news_ingestion_port: int = 8003
    archive_lookup_port: int = 8004
    parser_normalizer_port: int = 8005
    memory_port: int = 8006
    risk_stub_port: int = 8007
    audit_log_port: int = 8008
    execution_sim_port: int = 8009

    orchestrator_url: str = "http://orchestrator:8001"
    market_data_url: str = "http://market_data:8002"
    news_ingestion_url: str = "http://news_ingestion:8003"
    archive_lookup_url: str = "http://archive_lookup:8004"
    parser_normalizer_url: str = "http://parser_normalizer:8005"
    memory_url: str = "http://memory:8006"
    risk_stub_url: str = "http://risk_stub:8007"
    audit_log_url: str = "http://audit_log:8008"
    execution_sim_url: str = "http://execution_sim:8009"

    http_timeout_seconds: float = 12.0

    @property
    def sqlalchemy_database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=16)
def get_settings(service_name: str = "service") -> Settings:
    st = Settings(
        app_env=_env_str("APP_ENV", "local"),
        log_level=_env_str("LOG_LEVEL", "INFO"),
        service_name=service_name,
        postgres_host=_env_str("POSTGRES_HOST", "postgres"),
        postgres_port=_env_int("POSTGRES_PORT", 5432),
        postgres_db=_env_str("POSTGRES_DB", "trade_ai"),
        postgres_user=_env_str("POSTGRES_USER", "trade_ai"),
        postgres_password=_env_str("POSTGRES_PASSWORD", "trade_ai"),
        redis_url=_env_str("REDIS_URL", "redis://redis:6379/0"),
        qdrant_url=_env_str("QDRANT_URL", "http://qdrant:6333"),
        qdrant_collection=_env_str("QDRANT_COLLECTION", "documents"),
        openai_api_key=_env_str("OPENAI_API_KEY", ""),
        openai_model=_env_str("OPENAI_MODEL", "gpt-4.1"),
        newsapi_api_key=_env_str("NEWSAPI_API_KEY", ""),
        coinbase_api_key=_env_str("COINBASE_API_KEY", ""),
        coinbase_api_secret=_env_str("COINBASE_API_SECRET", ""),
        coinbase_api_passphrase=_env_str("COINBASE_API_PASSPHRASE", ""),
        coinbase_use_sandbox=_env_bool("COINBASE_USE_SANDBOX", True),
        live_custody_provider=_env_str("LIVE_CUSTODY_PROVIDER", "env"),
        live_custody_key_id=_env_str("LIVE_CUSTODY_KEY_ID", ""),
        live_custody_secret_id=_env_str("LIVE_CUSTODY_SECRET_ID", ""),
        live_custody_last_rotated_at=_env_str("LIVE_CUSTODY_LAST_ROTATED_AT", ""),
        live_custody_rotation_max_age_days=_env_int("LIVE_CUSTODY_ROTATION_MAX_AGE_DAYS", 90),
        wayback_base_url=_env_str("WAYBACK_BASE_URL", "https://archive.org"),
        commoncrawl_index_url=_env_str("COMMONCRAWL_INDEX_URL", "https://index.commoncrawl.org"),
        execution_enabled=_env_bool("EXECUTION_ENABLED", False),
        paper_trading_enabled=_env_bool("PAPER_TRADING_ENABLED", False),
        live_execution_sandbox_enabled=_env_bool("LIVE_EXECUTION_SANDBOX_ENABLED", False),
        live_execution_sandbox_transport_enabled=_env_bool("LIVE_EXECUTION_SANDBOX_TRANSPORT_ENABLED", False),
        live_execution_provider=_env_str("LIVE_EXECUTION_PROVIDER", "mock"),
        live_router_max_spread_bps=_env_float("LIVE_ROUTER_MAX_SPREAD_BPS", 120.0),
        live_router_max_estimated_cost_bps=_env_float("LIVE_ROUTER_MAX_ESTIMATED_COST_BPS", 180.0),
        live_router_fee_bps_coinbase=_env_float("LIVE_ROUTER_FEE_BPS_COINBASE", 8.0),
        live_router_fee_bps_binance=_env_float("LIVE_ROUTER_FEE_BPS_BINANCE", 10.0),
        live_router_fee_bps_kraken=_env_float("LIVE_ROUTER_FEE_BPS_KRAKEN", 16.0),
        live_router_alert_min_decisions=_env_int("LIVE_ROUTER_ALERT_MIN_DECISIONS", 20),
        live_router_alert_min_route_eligible_rate=_env_float("LIVE_ROUTER_ALERT_MIN_ROUTE_ELIGIBLE_RATE", 0.60),
        live_router_alert_min_feasible_route_rate=_env_float("LIVE_ROUTER_ALERT_MIN_FEASIBLE_ROUTE_RATE", 0.55),
        live_router_alert_max_spread_blocker_ratio=_env_float("LIVE_ROUTER_ALERT_MAX_SPREAD_BLOCKER_RATIO", 0.30),
        live_router_alert_max_cost_blocker_ratio=_env_float("LIVE_ROUTER_ALERT_MAX_COST_BLOCKER_RATIO", 0.30),
        live_router_retention_days=_env_int("LIVE_ROUTER_RETENTION_DAYS", 90),
        live_router_gate_retention_days=_env_int("LIVE_ROUTER_GATE_RETENTION_DAYS", 180),
        live_router_incident_retention_days=_env_int("LIVE_ROUTER_INCIDENT_RETENTION_DAYS", 180),
        live_execution_submission_retention_days=_env_int("LIVE_EXECUTION_SUBMISSION_RETENTION_DAYS", 180),
        paper_initial_usd_balance=_env_float("PAPER_INITIAL_USD_BALANCE", 100000.0),
        paper_market_slippage_bps=_env_float("PAPER_MARKET_SLIPPAGE_BPS", 5.0),
        paper_fee_bps=_env_float("PAPER_FEE_BPS", 0.0),
        paper_max_notional_usd=_env_float("PAPER_MAX_NOTIONAL_USD", 25000.0),
        paper_max_position_qty=_env_float("PAPER_MAX_POSITION_QTY", 100.0),
        paper_daily_loss_limit_usd=_env_float("PAPER_DAILY_LOSS_LIMIT_USD", 2000.0),
        paper_order_require_approval=_env_bool("PAPER_ORDER_REQUIRE_APPROVAL", False),
        paper_alert_drawdown_pct_threshold=_env_float("PAPER_ALERT_DRAWDOWN_PCT_THRESHOLD", 10.0),
        paper_alert_concentration_pct_threshold=_env_float("PAPER_ALERT_CONCENTRATION_PCT_THRESHOLD", 60.0),
        paper_min_performance_days=_env_int("PAPER_MIN_PERFORMANCE_DAYS", 7),
        paper_min_performance_points=_env_int("PAPER_MIN_PERFORMANCE_POINTS", 24),
        paper_retention_days=_env_int("PAPER_RETENTION_DAYS", 180),
        gateway_port=_env_int("GATEWAY_PORT", 8000),
        orchestrator_port=_env_int("ORCHESTRATOR_PORT", 8001),
        market_data_port=_env_int("MARKET_DATA_PORT", 8002),
        news_ingestion_port=_env_int("NEWS_INGESTION_PORT", 8003),
        archive_lookup_port=_env_int("ARCHIVE_LOOKUP_PORT", 8004),
        parser_normalizer_port=_env_int("PARSER_NORMALIZER_PORT", 8005),
        memory_port=_env_int("MEMORY_PORT", 8006),
        risk_stub_port=_env_int("RISK_STUB_PORT", 8007),
        audit_log_port=_env_int("AUDIT_LOG_PORT", 8008),
        execution_sim_port=_env_int("EXECUTION_SIM_PORT", 8009),
        orchestrator_url=_env_str("ORCHESTRATOR_URL", "http://orchestrator:8001"),
        market_data_url=_env_str("MARKET_DATA_URL", "http://market_data:8002"),
        news_ingestion_url=_env_str("NEWS_INGESTION_URL", "http://news_ingestion:8003"),
        archive_lookup_url=_env_str("ARCHIVE_LOOKUP_URL", "http://archive_lookup:8004"),
        parser_normalizer_url=_env_str("PARSER_NORMALIZER_URL", "http://parser_normalizer:8005"),
        memory_url=_env_str("MEMORY_URL", "http://memory:8006"),
        risk_stub_url=_env_str("RISK_STUB_URL", "http://risk_stub:8007"),
        audit_log_url=_env_str("AUDIT_LOG_URL", "http://audit_log:8008"),
        execution_sim_url=_env_str("EXECUTION_SIM_URL", "http://execution_sim:8009"),
        http_timeout_seconds=_env_float("HTTP_TIMEOUT_SECONDS", 12.0),
    )
    return st
