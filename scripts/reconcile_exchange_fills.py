#!/usr/bin/env python3
from __future__ import annotations

import json, os, sqlite3, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def data_dir() -> Path:
    from services.os.app_paths import data_dir as _dd
    return _dd()

def default_exec_db() -> str:
    from services.risk.risk_daily import _default_exec_db
    return _default_exec_db()

def write_flag(fill: dict, reason: str) -> None:
    flag = data_dir() / "risk_sink_failed.flag"
    flag.parent.mkdir(parents=True, exist_ok=True)
    tmp = flag.with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "failed_at": time.time(),
        "venue": fill.get("venue", "unknown"),
        "fill_id": fill.get("fill_id", "unknown"),
        "symbol": fill.get("symbol", "unknown"),
        "error": reason,
    }, sort_keys=True), encoding="utf-8")
    tmp.replace(flag)

def exists(exec_db: str, venue: str, fill_id: str) -> bool:
    con = sqlite3.connect(exec_db)
    try:
        row = con.execute(
            "SELECT 1 FROM canonical_fills WHERE venue=? AND fill_id=? LIMIT 1",
            (venue, fill_id),
        ).fetchone()
        return row is not None
    except sqlite3.OperationalError:
        return False
    finally:
        con.close()

def trade_to_fill(tr: dict, *, venue: str, symbol: str) -> dict:
    tid = str(tr.get("id") or tr.get("tradeId") or "")
    side = str(tr.get("side") or "").lower()
    qty = float(tr.get("amount") or tr.get("qty") or 0.0)
    price = float(tr.get("price") or 0.0)

    fee_obj = tr.get("fee") if isinstance(tr.get("fee"), dict) else {}
    fee_ccy = str(fee_obj.get("currency") or "").upper()
    fee_usd = float(fee_obj.get("cost") or 0.0) if fee_ccy in {"USD", "USDT", "USDC"} else 0.0

    fill = {
        "venue": venue,
        "fill_id": tid,
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "price": price,
        "ts": str(tr.get("datetime") or datetime.now(timezone.utc).isoformat()),
        "fee_usd": fee_usd,
        "client_order_id": str(tr.get("clientOrderId") or ""),
        "order_id": str(tr.get("order") or tr.get("orderId") or ""),
    }

    for k in ("realized_pnl_usd", "realized_pnl", "realizedPnl"):
        if tr.get(k) is not None:
            fill["realized_pnl_usd"] = float(tr[k])
            break
    return fill

def main() -> None:
    from services.execution.live_exchange_adapter import LiveExchangeAdapter
    from services.journal.fill_sink import CanonicalFillSink

    exec_db = os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH") or default_exec_db()
    venue = (os.environ.get("CBP_VENUE") or "").strip().lower()
    symbols = [s.strip() for s in (os.environ.get("CBP_SYMBOLS") or "").split(",") if s.strip()]
    lookback_ms = int(os.environ.get("CBP_RECONCILE_LOOKBACK_MS") or "600000")
    sandbox = os.environ.get("CBP_SANDBOX", "1").lower() not in {"0", "false", "no"}

    if not venue or not symbols:
        print("ERROR: set CBP_VENUE and CBP_SYMBOLS", file=sys.stderr)
        raise SystemExit(2)

    sink = CanonicalFillSink(exec_db=exec_db)
    total_missing = total_replayed = total_failures = 0

    ad = LiveExchangeAdapter(venue, sandbox=sandbox)
    try:
        for symbol in symbols:
            since_ms = int(time.time() * 1000) - lookback_ms
            trades = ad.fetch_my_trades(symbol, since_ms=since_ms, limit=500) or []
            print(f"{venue}/{symbol}: trades_seen={len(trades)}")

            for tr in trades:
                fill = trade_to_fill(tr, venue=venue, symbol=symbol)
                if not fill["fill_id"] or fill["side"] not in {"buy", "sell"} or fill["qty"] <= 0 or fill["price"] <= 0:
                    total_failures += 1
                    write_flag(fill, "invalid_exchange_trade")
                    print(f"FAIL invalid_trade fill={fill}")
                    raise SystemExit(1)

                if exists(exec_db, venue, fill["fill_id"]):
                    continue

                total_missing += 1
                result = sink.on_fill(fill)

                if not isinstance(result, dict):
                    total_failures += 1
                    write_flag(fill, "fill_sink_return_contract_missing")
                    print("FAIL fill_sink_return_contract_missing")
                    raise SystemExit(1)

                if not result.get("ok"):
                    total_failures += 1
                    write_flag(fill, str(result.get("reason") or "sink_failed"))
                    print(f"FAIL sink_failed fill_id={fill['fill_id']} result={result}")
                    raise SystemExit(1)

                total_replayed += 1

    finally:
        try:
            ad.close()
        except Exception:
            pass

    print(f"TOTAL missing_detected={total_missing}")
    print(f"TOTAL replayed={total_replayed}")
    print(f"TOTAL failures={total_failures}")
    raise SystemExit(0)

if __name__ == "__main__":
    main()
