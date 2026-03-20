from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RiskLimit(Base):
    __tablename__ = "risk_limits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    risk_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("risk_profiles.id"), nullable=True)
    max_position_size_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_daily_loss_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_weekly_loss_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_portfolio_exposure_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_leverage: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_asset_concentration_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_correlated_exposure_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    min_confidence: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_slippage_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_spread_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    min_liquidity_usd: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    approval_required_for_live: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    approval_required_above_size_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    approval_required_for_low_confidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    approval_required_for_futures: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RiskStatusSnapshot(Base):
    __tablename__ = "risk_status_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    risk_status: Mapped[str] = mapped_column(String, nullable=False)
    exposure_used_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    drawdown_today_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    drawdown_week_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    leverage: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    blocked_trades_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_warnings_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    related_type: Mapped[str | None] = mapped_column(String, nullable=True)
    related_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False, default="warning")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KillSwitchEvent(Base):
    __tablename__ = "kill_switch_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RestrictedAsset(Base):
    __tablename__ = "restricted_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    asset_symbol: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


OWNED_MODELS = (
    RiskProfile,
    RiskLimit,
    RiskStatusSnapshot,
    RiskEvent,
    KillSwitchEvent,
    RestrictedAsset,
)
