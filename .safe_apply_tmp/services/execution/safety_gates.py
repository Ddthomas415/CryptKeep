from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from storage.market_ws_store_sqlite import SQLiteMarketWsStore


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass(frozen=True)
class SafetyConfig:
    enabled: bool = True
    # Market freshness: last message recv age (not server age)
    max_ws_recv_age_ms: int = 1500
    # Execution ack: submit->ack max; if exceeded too often, pause (runner decides)
    max_ack_ms: int = 3000
    pause_seconds_on_breach: int = 30
    require_ws_fresh_for_live: bool = True
    latency_db_path: str = "data/market_ws.sqlite"


def check_market_freshness(store: SQLiteMarketWsStore, exchange: str, symbols: List[str], max_recv_age_ms: int) -> Tuple[bool, Dict[str, Any]]:
    now = now_ms()
    per = []
    ok = True
    for s in symbols:
        last = store.last_tob(exchange=exchange, symbol=s)
        if not last:
            ok = False
            per.append({"symbol": s, "ok": False, "reason": "no_ws_data"})
            continue
        recv_ts = int(last.get("recv_ts_ms") or 0)
        recv_age = now - recv_ts if recv_ts else 10**9
        if recv_age > int(max_recv_age_ms):
            ok = False
            per.append({"symbol": s, "ok": False, "recv_age_ms": recv_age})
        else:
            per.append({"symbol": s, "ok": True, "recv_age_ms": recv_age})
    return ok, {"exchange": exchange, "max_ws_recv_age_ms": max_recv_age_ms, "per_symbol": per}
