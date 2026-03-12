import uuid

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class RiskLimit(Base):
    __tablename__ = "risk_limits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    max_position_size_pct: Mapped[float] = mapped_column(Float, default=2.0)
    max_daily_loss_pct: Mapped[float] = mapped_column(Float, default=3.0)
    max_weekly_loss_pct: Mapped[float] = mapped_column(Float, default=7.0)
    max_portfolio_exposure_pct: Mapped[float] = mapped_column(Float, default=35.0)
    max_leverage: Mapped[float] = mapped_column(Float, default=2.0)
    max_asset_concentration_pct: Mapped[float] = mapped_column(Float, default=20.0)
    max_correlated_exposure_pct: Mapped[float] = mapped_column(Float, default=30.0)
    min_confidence: Mapped[float] = mapped_column(Float, default=0.65)
    max_slippage_pct: Mapped[float] = mapped_column(Float, default=0.4)
    max_spread_pct: Mapped[float] = mapped_column(Float, default=0.25)
    min_liquidity_usd: Mapped[float] = mapped_column(Float, default=1_000_000.0)

    approval_required_for_live: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_required_above_size_pct: Mapped[float] = mapped_column(Float, default=1.0)
    approval_required_for_low_confidence: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_required_for_futures: Mapped[bool] = mapped_column(Boolean, default=True)

    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RiskStatusSnapshot(Base):
    __tablename__ = "risk_status_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    ts: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    risk_status: Mapped[str] = mapped_column(String(20), nullable=False, default="safe")
    exposure_used_pct: Mapped[float] = mapped_column(Float, default=0.0)
    drawdown_today_pct: Mapped[float] = mapped_column(Float, default=0.0)
    drawdown_week_pct: Mapped[float] = mapped_column(Float, default=0.0)
    leverage: Mapped[float] = mapped_column(Float, default=1.0)
    blocked_trades_count: Mapped[int] = mapped_column(Integer, default=0)
    active_warnings_json: Mapped[list | None] = mapped_column(JSON, nullable=True)


class KillSwitchEvent(Base):
    __tablename__ = "kill_switch_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    changed_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
