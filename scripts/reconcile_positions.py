#!/usr/bin/env python3
from __future__ import annotations

import json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def data_dir() -> Path:
    from services.os.app_paths import data_dir as _dd
    return _dd()

def default_exec_db() -> str:
    from services.risk.risk_daily import _default_exec_db
    return _default_exec_db()

def write_flag(venue: str, symbol: str, drift: float, reason: str) -> None:
    flag = data_dir() / "risk_sink_failed.flag"
    flag.parent.mkdir(parents=True, exist_ok=True)
    tmp = flag.with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "failed_at": time.time(),
        "venue": venue,
        "fill_id": "position_drift",
        "symbol": symbol,
        "drift": drift,
        "error": reason,
    }, sort_keys=True), encoding="utf-8")
    tmp.replace(flag)

def exchange_qty_from_balance(balance: dict, symbol: str) -> float:
    base = symbol.split("/")[0].upper()
    total = balance.get("total")
    if isinstance(total, dict) and total.get(base) is not None:
        return float(total.get(base) or 0.0)
    entry = balance.get(symbol) or balance.get(base)
    if isinstance(entry, dict) and entry.get("total") is not None:
        return float(entry.get("total") or 0.0)
    return 0.0

def main() -> None:
    from services.execution.live_exchange_adapter import LiveExchangeAdapter
    from storage.live_position_store_sqlite import LivePositionStore

    exec_db = os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH") or default_exec_db()
    venue = (os.environ.get("CBP_VENUE") or "").strip().lower()
    symbols = [s.strip() for s in (os.environ.get("CBP_SYMBOLS") or "").split(",") if s.strip()]
    threshold = float(os.environ.get("CBP_POSITION_DRIFT_THRESHOLD") or "0.0001")
    sandbox = os.environ.get("CBP_SANDBOX", "1").lower() not in {"0", "false", "no"}

    if not venue or not symbols:
        print("ERROR: set CBP_VENUE and CBP_SYMBOLS", file=sys.stderr)
        raise SystemExit(2)

    print("NOTE: spot-only drift detector; does not support derivatives/margin positions")

    ad = LiveExchangeAdapter(venue, sandbox=sandbox)
    try:
        balance = ad.fetch_balance()
    finally:
        try:
            ad.close()
        except Exception:
            pass

    store = LivePositionStore(exec_db=exec_db)

    for symbol in symbols:
        xqty = exchange_qty_from_balance(balance, symbol)
        result = store.reconcile_to_exchange(
            venue=venue,
            symbol=symbol,
            exchange_qty=xqty,
            tolerance=threshold,
        )

        print(
            f"{venue}/{symbol}: local={result['local_qty']} exchange={result['exchange_qty']} "
            f"drift={result['drift']} tolerance={result['tolerance']} ok={result['ok']}"
        )

        if not result["ok"]:
            reason = (
                f"position_drift local={result['local_qty']} exchange={result['exchange_qty']} "
                f"drift={result['drift']} threshold={threshold}"
            )
            write_flag(venue, symbol, float(result["drift"]), reason)
            print("DRIFT DETECTED: risk_sink_failed.flag written")
            raise SystemExit(1)

    print("All spot positions within tolerance")
    raise SystemExit(0)

if __name__ == "__main__":
    main()
