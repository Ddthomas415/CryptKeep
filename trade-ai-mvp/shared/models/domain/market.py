from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base
from shared.models.market import MarketCandle, MarketSnapshot, MarketTick


class MarketOrderbookSummary(Base):
    __tablename__ = "market_orderbook_summary"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    best_bid: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    best_ask: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    spread: Mapped[float | None] = mapped_column(Numeric(20, 8), nullable=True)
    depth_1pct: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    depth_2pct: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    imbalance: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    raw_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


OWNED_MODELS = (
    MarketCandle,
    MarketTick,
    MarketSnapshot,
    MarketOrderbookSummary,
)
