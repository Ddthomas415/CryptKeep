# Phase 188: Persisted WS health logger
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from storage.ws_status_sqlite import WSStatusSQLite


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def log_ws_health(
    *,
    exchange: str,
    symbol: str,
    connected: bool,
    recv_ts_ms: int,
    lag_ms: float | None = None,
    error: str | None = None,
    meta: Dict[str, Any] | None = None,
    store: WSStatusSQLite | None = None,
) -> Dict[str, Any]:
    db = store or WSStatusSQLite()
    lag = float(lag_ms) if lag_ms is not None else max(0.0, float(_now_ms() - int(recv_ts_ms)))
    status = "ok" if connected and not error else "error"
    db.upsert_status(
        exchange=str(exchange),
        symbol=str(symbol),
        status=status,
        recv_ts_ms=int(recv_ts_ms),
        lag_ms=float(lag),
        error=error,
        meta=meta or {},
    )
    return {"ok": True, "exchange": str(exchange), "symbol": str(symbol), "status": status, "lag_ms": float(lag)}


def recent_ws_health(*, limit: int = 200, exchange: str | None = None, symbol: str | None = None) -> Dict[str, Any]:
    rows = WSStatusSQLite().recent_events(limit=int(limit), exchange=exchange, symbol=symbol)
    err = sum(1 for r in rows if str(r.get("status")) == "error")
    return {"ok": True, "count": len(rows), "error_count": err, "rows": rows}
