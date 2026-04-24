from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.security.exchange_factory import make_exchange
from services.signals.candidate_advisor import get_top_candidate
from services.strategies.strategy_selector import select_strategy


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare candidate advisor vs runner selector")
    p.add_argument("--symbol", type=str, default=None, help="Override symbol; default is top candidate")
    p.add_argument("--timeframe", type=str, default="1h", help="OHLCV timeframe")
    p.add_argument("--limit", type=int, default=160, help="Fetch limit")
    p.add_argument("--min-score", type=float, default=35.0, help="Candidate advisor minimum score")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    top = get_top_candidate(min_score=float(args.min_score))
    if args.symbol:
        symbol = str(args.symbol)
    else:
        if not top:
            print({"error": "no_top_candidate"})
            return
        symbol = str(top.get("symbol"))

    ex = make_exchange("coinbase", {"apiKey": None, "secret": None}, enable_rate_limit=True)
    try:
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=str(args.timeframe), limit=int(args.limit))
    finally:
        if hasattr(ex, "close"):
            ex.close()

    runner_pick = select_strategy(
        default_strategy="ema_cross",
        ohlcv=ohlcv[-120:],
    )

    print("=== candidate advisor ===")
    print(top if top and top.get("symbol") == symbol else {
        "symbol": symbol,
        "top_candidate": top,
    })

    print("\n=== runner selector ===")
    print(runner_pick)


if __name__ == "__main__":
    main()
