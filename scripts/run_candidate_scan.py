from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.security.exchange_factory import make_exchange
from services.os.app_paths import runtime_dir
from services.signals.candidate_engine import build_candidate_list


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run CryptKeep candidate scan")
    p.add_argument(
        "--symbols",
        type=str,
        default="DOGE/USD,LTC/USD,ORCA/USD,ADA/EUR,LINK/EUR,AVAX/EUR,XRP/EUR",
        help="Comma-separated symbol list",
    )
    p.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="OHLCV timeframe, e.g. 15m, 1h",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=160,
        help="Fetch limit",
    )
    p.add_argument(
        "--min-score",
        type=float,
        default=40.0,
        help="Minimum composite score to keep",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    symbols = [s.strip() for s in str(args.symbols).split(",") if s.strip()]
    tf = str(args.timeframe)
    limit = int(args.limit)
    min_score = float(args.min_score)

    ex = make_exchange("coinbase", {"apiKey": None, "secret": None}, enable_rate_limit=True)
    rows = []
    try:
        for sym in symbols:
            ohlcv = ex.fetch_ohlcv(sym, timeframe=tf, limit=limit)
            closes = [float(r[4]) for r in ohlcv if len(r) >= 6]
            ret = 0.0
            if len(closes) >= 25 and closes[-25] > 0:
                ret = ((closes[-1] - closes[-25]) / closes[-25]) * 100.0
            rows.append({
                "symbol": sym,
                "ohlcv": ohlcv[-120:],
                "symbol_return_pct": ret,
            })
    finally:
        if hasattr(ex, "close"):
            ex.close()

    candidates = build_candidate_list(symbols_data=rows, min_composite_score=min_score)

    outdir = runtime_dir() / "candidates"
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / "latest_candidates.json"
    outfile.write_text(json.dumps(candidates, indent=2), encoding="utf-8")

    print(f"WROTE: {outfile}")
    for row in candidates:
        print(row)


if __name__ == "__main__":
    main()
