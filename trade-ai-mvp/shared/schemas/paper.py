from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PaperOrderCreateRequest(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"] = "market"
    quantity: float = Field(gt=0)
    limit_price: float | None = Field(default=None, gt=0)
    client_order_id: str | None = None
    time_in_force: str = "GTC"
    signal_source: str | None = None
    rationale: str | None = None
    catalyst_tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaperOrderOut(BaseModel):
    id: str
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    status: str
    quantity: float
    limit_price: float | None = None
    filled_quantity: float
    average_fill_price: float | None = None
    risk_gate: str | None = None
    signal_source: str | None = None
    rationale: str | None = None
    catalyst_tags: list[str] = Field(default_factory=list)
    execution_disabled: bool = True
    paper_mode: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    canceled_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaperOrderCancelResponse(BaseModel):
    canceled: bool
    order: PaperOrderOut


class PaperOrderListResponse(BaseModel):
    orders: list[PaperOrderOut] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False


class PaperFillOut(BaseModel):
    id: str
    order_id: str
    symbol: str
    side: str
    price: float
    quantity: float
    fee: float
    liquidity: str | None = None
    created_at: datetime | None = None


class PaperFillListResponse(BaseModel):
    fills: list[PaperFillOut] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False


class PaperPositionOut(BaseModel):
    symbol: str
    quantity: float
    avg_entry_price: float | None = None
    realized_pnl: float
    updated_at: datetime | None = None


class PaperMarkedPositionOut(BaseModel):
    symbol: str
    quantity: float
    avg_entry_price: float | None = None
    mark_price: float
    notional_usd: float
    unrealized_pnl: float


class PaperBalanceOut(BaseModel):
    asset: str
    balance: float
    available: float
    updated_at: datetime | None = None


class PaperEquityPointOut(BaseModel):
    ts: datetime
    equity: float
    cash: float
    unrealized_pnl: float
    realized_pnl: float
    note: str | None = None


class PaperEquitySnapshotResponse(PaperEquityPointOut):
    pass


class PaperEquitySeriesResponse(BaseModel):
    points: list[PaperEquityPointOut] = Field(default_factory=list)


class PaperPerformanceResponse(BaseModel):
    as_of: datetime
    points: int
    period_start: datetime | None = None
    start_equity: float | None = None
    end_equity: float | None = None
    return_pct: float | None = None
    high_watermark: float | None = None
    low_equity: float | None = None
    max_drawdown_usd: float | None = None
    max_drawdown_pct: float | None = None
    benchmark_name: str | None = None
    benchmark_return_pct: float | None = None
    excess_return_pct: float | None = None
    sharpe_proxy: float | None = None
    hit_rate: float | None = None
    hit_rate_by_regime: dict[str, float] = Field(default_factory=dict)


class PaperPerformanceRollupOut(BaseModel):
    interval: str
    bucket_start: datetime
    bucket_end: datetime
    points: int
    start_equity: float
    end_equity: float
    return_pct: float | None = None
    high_watermark: float | None = None
    low_equity: float | None = None
    max_drawdown_usd: float | None = None
    max_drawdown_pct: float | None = None
    benchmark_name: str | None = None
    benchmark_return_pct: float | None = None
    excess_return_pct: float | None = None


class PaperPerformanceRollupListResponse(BaseModel):
    rollups: list[PaperPerformanceRollupOut] = Field(default_factory=list)


class PaperPerformanceRollupRefreshResponse(BaseModel):
    interval: str
    refreshed: int


class PaperReadinessResponse(BaseModel):
    as_of: datetime
    phase3_live_eligible: bool
    reason: str
    min_days_required: int
    min_points_required: int
    observed_days: float
    observed_points: int
    return_pct: float | None = None
    max_drawdown_pct: float | None = None
    sharpe_proxy: float | None = None


class PaperRetentionResponse(BaseModel):
    as_of: datetime
    retention_days: int
    deleted_fills: int
    deleted_orders: int
    deleted_equity_points: int
    deleted_rollups: int


class PaperReplayRequest(BaseModel):
    symbol: str = "SOL-USD"
    start: datetime | None = None
    end: datetime | None = None
    entry_bps: float = 10.0
    hold_steps: int = 1


class PaperReplayResponse(BaseModel):
    symbol: str
    strategy: str
    start: datetime | None = None
    end: datetime | None = None
    points: int
    trades: int
    gross_return_pct: float
    max_drawdown_pct: float
    status: str


class PaperShadowCompareRequest(BaseModel):
    symbol: str = "SOL-USD"
    start: datetime | None = None
    end: datetime | None = None
    champion_entry_bps: float = 10.0
    challenger_entry_bps: float = 5.0
    hold_steps: int = 1


class PaperShadowCompareResponse(BaseModel):
    symbol: str
    start: datetime | None = None
    end: datetime | None = None
    points: int
    champion_return_pct: float
    challenger_return_pct: float
    delta_return_pct: float
    champion_trades: int
    challenger_trades: int
    winner: str
    status: str


class PaperPortfolioSummaryResponse(BaseModel):
    as_of: datetime
    cash: float
    realized_pnl: float
    unrealized_pnl: float
    equity: float
    gross_exposure_usd: float
    positions: list[PaperMarkedPositionOut] = Field(default_factory=list)


class PaperRiskEnvelope(BaseModel):
    gate: str
    approved: bool
    paper_approved: bool
    reason: str
