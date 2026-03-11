from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, PrimaryKeyConstraint, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base


class MarketCandle(Base):
    __tablename__ = "market_candles"
    __table_args__ = (
        PrimaryKeyConstraint("ts", "exchange", "symbol", "interval", name="pk_market_candles"),
    )

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    interval: Mapped[str] = mapped_column(String, nullable=False)
    open: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    quote_volume: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    trades_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class MarketTick(Base):
    __tablename__ = "market_ticks"
    __table_args__ = (
        PrimaryKeyConstraint("ts", "exchange", "symbol", "trade_id", name="pk_market_ticks"),
    )

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    size: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    side: Mapped[str | None] = mapped_column(String, nullable=True)
    trade_id: Mapped[str] = mapped_column(Text, nullable=False)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    last_price: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    bid: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    ask: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    spread: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    funding_rate: Mapped[float | None] = mapped_column(Numeric(12, 8), nullable=True)
    open_interest: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
