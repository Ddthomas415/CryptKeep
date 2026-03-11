from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class WSClientStatus:
    exchange: str
    symbol: str
    connected: bool
    recv_ts_ms: int
    lag_ms: float
    note: str = ""


def build_status(*, exchange: str, symbol: str, connected: bool, recv_ts_ms: int, now_ts_ms: int | None = None, note: str = "") -> Dict[str, Any]:
    now = int(now_ts_ms) if now_ts_ms is not None else int(datetime.now(timezone.utc).timestamp() * 1000)
    lag = max(0.0, float(now - int(recv_ts_ms)))
    return {
        "exchange": str(exchange).lower().strip(),
        "symbol": str(symbol).strip(),
        "connected": bool(connected),
        "recv_ts_ms": int(recv_ts_ms),
        "lag_ms": float(lag),
        "ts": datetime.now(timezone.utc).isoformat(),
        "note": str(note),
    }
