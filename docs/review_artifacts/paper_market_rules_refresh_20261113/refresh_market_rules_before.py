from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)
import argparse
import json
from services.markets.rules import fetch_and_cache
from services.markets.symbols import canonicalize
from services.markets.cache_sqlite import default_exec_db

DEFAULT = {
    "binance": ["BTC-USD", "ETH-USD"],
    "gate": ["BTC-USD", "ETH-USD"],
    "coinbase": ["BTC-USD", "ETH-USD"],
}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="", help="binance|gate|coinbase")
    ap.add_argument("--exchange", default="", help="alias for --venue")
    ap.add_argument("--symbols", default="", help="comma-separated canonical symbols")
    ap.add_argument("--symbol", default="", help="alias: single symbol")
    args = ap.parse_args()

    exec_db = default_exec_db()
    v = (args.venue or args.exchange).lower().strip()
    raw = args.symbols.strip() or args.symbol.strip()
    symbols = [canonicalize(x) for x in raw.split(",") if x.strip()] if raw else DEFAULT.get(v, ["BTC-USD"])

    out=[]
    for s in symbols:
        r = fetch_and_cache(exec_db, v, s)
        out.append({"venue": v, "symbol": s, "active": r.active, "native": r.native_symbol, "min_notional": r.min_notional, "min_qty": r.min_qty, "qty_step": r.qty_step})
    print(json.dumps({"ok": True, "exec_db": exec_db, "results": out}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
