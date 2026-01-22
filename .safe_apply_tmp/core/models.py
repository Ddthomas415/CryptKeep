from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class TimeInForce(str, Enum):
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"
    POST_ONLY = "post_only"


class OrderStatus(str, Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass(frozen=True)
class Intent:
    """Strategy output (NOT an order)."""
    strategy: str
    venue: str
    symbol: str
    target_qty: float
    max_slippage_bps: float = 10.0
    urgency: float = 0.5  # 0..1
    ts: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Order:
    """Exchange order request (idempotent via client_order_id)."""
    venue: str
    symbol: str
    side: Side
    order_type: OrderType
    qty: float
    client_order_id: str
    limit_price: Optional[float] = None
    tif: TimeInForce = TimeInForce.GTC
    reduce_only: bool = False
    post_only: bool = False
    ts: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class OrderAck:
    client_order_id: str
    venue_order_id: Optional[str]
    status: OrderStatus
    message: Optional[str] = None
    ts: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Fill:
    venue: str
    symbol: str
    side: Side
    qty: float
    price: float
    fee: float
    client_order_id: str
    venue_order_id: Optional[str]
    fill_id: Optional[str] = None
    ts: datetime = field(default_factory=utc_now)


@dataclass
class Position:
    venue: str
    symbol: str
    qty: float = 0.0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class PortfolioState:
    ts: datetime = field(default_factory=utc_now)
    cash: float = 0.0
    equity: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)  # key: f"{venue}:{symbol}"


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: Optional[str] = None
    max_qty: Optional[float] = None
    max_notional: Optional[float] = None
