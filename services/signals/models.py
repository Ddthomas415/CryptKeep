from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any
from datetime import datetime, timezone
import uuid

Action = Literal["buy","sell","hold"]

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class SignalEvent:
    signal_id: str
    ts: str  # ISO string preferred
    source: str  # e.g. "tradingview_alert", "manual_import", "discord", "telegram"
    author: str  # public handle or label (not a private identity)
    venue_hint: str  # e.g. "binance" / "coinbase" / "gateio" or "" for unknown
    symbol: str  # canonical symbol e.g. BTC/USDT or BTC/USD
    action: Action
    confidence: float  # 0..1
    notes: str
    raw: Dict[str, Any]

def new_id() -> str:
    return str(uuid.uuid4())
