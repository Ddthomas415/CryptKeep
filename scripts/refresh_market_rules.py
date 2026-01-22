from __future__ import annotations
import argparse, json
from services.markets.rules import fetch_and_cache
from services.markets.symbols import canonicalize
from services.markets.cache_sqlite import default_exec_db

DEFAULT = {
    "binance": ["BTC-USDT", "ETH-USDT"],
    "gate": ["BTC-USDT", "ETH-USDT"],
    "coinbase": ["BTC-USD", "ETH-USD"],
}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", required=True, help="binance|gate|coinbase")
    ap.add_argument("--symbols", default="", help="comma-separated canonical symbols")
    args = ap.parse_args()

    exec_db = default_exec_db()
    v = args.venue.lower().strip()
    symbols = [canonicalize(x) for x in args.symbols.split(",") if x.strip()] if args.symbols.strip() else DEFAULT.get(v, ["BTC-USDT"])

    out=[]
    for s in symbols:
        r = fetch_and_cache(exec_db, v, s)
        out.append({"venue": v, "symbol": s, "active": r.active, "native": r.native_symbol, "min_notional": r.min_notional, "min_qty": r.min_qty, "qty_step": r.qty_step})
    print(json.dumps({"ok": True, "exec_db": exec_db, "results": out}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
