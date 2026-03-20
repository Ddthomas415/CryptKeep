from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, PrimaryKeyConstraint, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base


class PaperOrder(Base):
    __tablename__ = "paper_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_order_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    order_type: Mapped[str] = mapped_column(String, nullable=False, default="market")
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    limit_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    filled_quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False, default=0)
    average_fill_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    risk_gate: Mapped[str | None] = mapped_column(String, nullable=True)
    signal_source: Mapped[str | None] = mapped_column(String, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    catalyst_tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PaperFill(Base):
    __tablename__ = "paper_fills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("paper_orders.id", ondelete="CASCADE"), nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    fee: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    liquidity: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False, default=0)
    avg_entry_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    realized_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PaperBalance(Base):
    __tablename__ = "paper_balances"

    asset: Mapped[str] = mapped_column(String, primary_key=True)
    balance: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False, default=0)
    available: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PaperEquityPoint(Base):
    __tablename__ = "paper_equity_curve"
    __table_args__ = (PrimaryKeyConstraint("ts", name="pk_paper_equity_curve"),)

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    equity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    cash: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    realized_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class PaperPerformanceRollup(Base):
    __tablename__ = "paper_performance_rollups"
    __table_args__ = (
        PrimaryKeyConstraint("interval", "bucket_start", name="pk_paper_performance_rollups"),
    )

    interval: Mapped[str] = mapped_column(String, nullable=False)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bucket_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    points: Mapped[int] = mapped_column(nullable=False)
    start_equity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    end_equity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    return_pct: Mapped[float | None] = mapped_column(Numeric(16, 8), nullable=True)
    high_watermark: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    low_equity: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    max_drawdown_usd: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Numeric(16, 8), nullable=True)
    benchmark_name: Mapped[str | None] = mapped_column(String, nullable=True)
    benchmark_return_pct: Mapped[float | None] = mapped_column(Numeric(16, 8), nullable=True)
    excess_return_pct: Mapped[float | None] = mapped_column(Numeric(16, 8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
