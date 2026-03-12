from pydantic import BaseModel, Field


class RiskSummary(BaseModel):
    risk_status: str
    exposure_used_pct: float
    drawdown_today_pct: float
    drawdown_week_pct: float
    leverage: float
    blocked_trades_count: int
    active_warnings: list[str]

    @classmethod
    def example(cls) -> dict:
        return cls(
            risk_status="safe",
            exposure_used_pct=18.4,
            drawdown_today_pct=0.8,
            drawdown_week_pct=1.2,
            leverage=1.0,
            blocked_trades_count=2,
            active_warnings=[],
        ).model_dump()


class RiskLimits(BaseModel):
    max_position_size_pct: float = Field(default=2.0, ge=0)
    max_daily_loss_pct: float = Field(default=3.0, ge=0)
    max_weekly_loss_pct: float = Field(default=7.0, ge=0)
    max_portfolio_exposure_pct: float = Field(default=35.0, ge=0)
    max_leverage: float = Field(default=2.0, ge=0)
    max_asset_concentration_pct: float = Field(default=20.0, ge=0)
    min_confidence: float = Field(default=0.65, ge=0, le=1)
    max_slippage_pct: float = Field(default=0.4, ge=0)
    max_spread_pct: float = Field(default=0.25, ge=0)
    min_liquidity_usd: float = Field(default=1_000_000.0, ge=0)

    @classmethod
    def default(cls) -> dict:
        return cls().model_dump()


class RiskLimitsUpdate(BaseModel):
    max_position_size_pct: float | None = Field(default=None, ge=0)
    max_daily_loss_pct: float | None = Field(default=None, ge=0)
    max_weekly_loss_pct: float | None = Field(default=None, ge=0)
    max_portfolio_exposure_pct: float | None = Field(default=None, ge=0)
    max_leverage: float | None = Field(default=None, ge=0)
    max_asset_concentration_pct: float | None = Field(default=None, ge=0)
    min_confidence: float | None = Field(default=None, ge=0, le=1)
    max_slippage_pct: float | None = Field(default=None, ge=0)
    max_spread_pct: float | None = Field(default=None, ge=0)
    min_liquidity_usd: float | None = Field(default=None, ge=0)
