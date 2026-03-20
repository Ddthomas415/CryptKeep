from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    asset_symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    strategy_name: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    entry_zone: Mapped[str | None] = mapped_column(String, nullable=True)
    stop_level: Mapped[str | None] = mapped_column(String, nullable=True)
    target_logic: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_size_pct: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    approval_required: Mapped[bool] = mapped_column(nullable=False, default=True)
    execution_disabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    mode_compatibility_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ready")
    thesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    invalidation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RecommendationVersion(Base):
    __tablename__ = "recommendation_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    exchange_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exchange_connections.id"),
        nullable=True,
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=True)
    approval_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("approvals.id"), nullable=True)
    asset_symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    order_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="created")
    external_order_id: Mapped[str | None] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Fill(Base):
    __tablename__ = "fills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    exchange_fill_id: Mapped[str | None] = mapped_column(String, nullable=True)
    fill_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    fill_size: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    fee: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    fee_asset: Mapped[str | None] = mapped_column(String, nullable=True)
    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True)
    exchange_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exchange_connections.id"),
        nullable=True,
    )
    asset_symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    avg_entry: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    mark_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    realized_pnl: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    unrealized_pnl: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    stop_level: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    target_level: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    strategy_name: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=False, default="open")
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PositionSnapshot(Base):
    __tablename__ = "position_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    mark_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    unrealized_pnl: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    size: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    exposure_value: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)


OWNED_MODELS = (
    Recommendation,
    RecommendationVersion,
    Approval,
    Order,
    Fill,
    Position,
    PositionSnapshot,
)
