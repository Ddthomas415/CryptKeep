from pydantic import BaseModel


class PortfolioSummary(BaseModel):
    total_value: float
    cash: float
    unrealized_pnl: float
    realized_pnl_24h: float | None = None
    exposure_used_pct: float | None = None
    leverage: float | None = None


class ConnectionsSummary(BaseModel):
    connected_exchanges: int
    connected_providers: int
    failed: int
    last_sync: str | None = None


class WatchlistItem(BaseModel):
    asset: str
    price: float
    change_24h_pct: float
    volume_trend: str | None = None
    signal: str | None = None


class DashboardSummary(BaseModel):
    mode: str
    execution_enabled: bool
    approval_required: bool
    risk_status: str
    kill_switch: bool
    portfolio: PortfolioSummary
    connections: ConnectionsSummary | None = None
    watchlist: list[WatchlistItem] | None = None
    recent_explanations: list[dict] | None = None
    recommendations: list[dict] | None = None
    upcoming_catalysts: list[dict] | None = None

    @classmethod
    def example(cls) -> dict:
        return cls(
            mode="research_only",
            execution_enabled=False,
            approval_required=True,
            risk_status="safe",
            kill_switch=False,
            portfolio=PortfolioSummary(
                total_value=12450.35,
                cash=8200.12,
                unrealized_pnl=210.45,
                realized_pnl_24h=56.12,
                exposure_used_pct=18.4,
                leverage=1.0,
            ),
            connections=ConnectionsSummary(
                connected_exchanges=1,
                connected_providers=4,
                failed=0,
                last_sync="2026-03-11T13:05:00Z",
            ),
            watchlist=[
                WatchlistItem(
                    asset="BTC",
                    price=84250.12,
                    change_24h_pct=2.4,
                    volume_trend="high",
                    signal="watch",
                ),
                WatchlistItem(
                    asset="SOL",
                    price=187.42,
                    change_24h_pct=6.9,
                    volume_trend="high",
                    signal="research",
                ),
            ],
            recent_explanations=[],
            recommendations=[],
            upcoming_catalysts=[],
        ).model_dump()
