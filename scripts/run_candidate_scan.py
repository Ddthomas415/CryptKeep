from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.security.exchange_factory import make_exchange
from services.signals.candidate_engine import build_candidate_list


def main() -> None:
    symbols = ["DOGE/USD", "LTC/USD", "ORCA/USD", "ADA/EUR", "LINK/EUR", "AVAX/EUR", "XRP/EUR"]
    tf = "1h"
    limit = 160

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

    candidates = build_candidate_list(symbols_data=rows, min_composite_score=40.0)
    for row in candidates:
        print(row)


if __name__ == "__main__":
    main()
