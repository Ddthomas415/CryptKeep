"""Exploratory signal-only comparison; never campaign or promotion evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from services.strategies.es_daily_trend import compute_signal, signal_from_ohlcv


def compare(rows, *, fee_bps=10.0, slippage_bps=5.0, regime_entry=False, two_close_entry=False, reporting_currency="USD"):
    if reporting_currency not in ("USD", "USDT"):
        raise ValueError("unsupported reporting currency")
    if not rows or len(rows) <= 200:
        raise ValueError("need more than 200 daily bars")
    if any(not math.isfinite(x) or x < 0 or x >= 10000 for x in (fee_bps, slippage_bps)):
        raise ValueError("invalid cost assumptions")
    for i, row in enumerate(rows):
        ts, o, h, lo, c, _ = row
        if not all(math.isfinite(x) and x > 0 for x in (o, h, lo, c)) or not lo <= min(o, c) <= max(o, c) <= h:
            raise ValueError("invalid OHLC")
        if i and ts - rows[i - 1][0] != 86400000:
            raise ValueError("non-contiguous daily archive")
    outputs = {}
    for arm in ("sma200_signal_only", "buy_hold", "cash"):
        cash, qty, fees, peak, dd, basis = 1000.0, 0.0, 0.0, 1000.0, 0.0, 0.0
        trades, curve, closed, exposure = [], [], [], []
        f, s = fee_bps / 10000, slippage_bps / 10000
        for i in range(200, len(rows)):
            ts, o, _, _, close, _ = rows[i]
            # Only prior completed closes are available at this bar's open.
            long = arm == "buy_hold" or (arm == "sma200_signal_only" and
                    compute_signal([r[4] for r in rows[i-200:i]], period=200) == "long")
            entry_allowed = True
            if two_close_entry and arm == "sma200_signal_only" and long and qty == 0:
                entry_allowed = i >= 201 and compute_signal(
                    [r[4] for r in rows[i-201:i-1]], period=200
                ) == "long"
            if regime_entry and arm == "sma200_signal_only" and long and qty == 0:
                entry_allowed = entry_allowed and signal_from_ohlcv(rows[max(0,i-220):i], emit_evidence=False)["action"] == "buy"
            if long and entry_allowed and qty == 0 and arm != "cash":
                notional = min(100.0, cash / (1 + f))
                qty = notional / (o * (1 + s))
                fee = notional * f
                basis = notional + fee
                cash -= basis
                fees += fee
                trades.append({"ts": ts, "side": "buy", "price": o*(1+s), "qty": qty})
            elif not long and qty > 0:
                proceeds = qty * o * (1 - s)
                fee = proceeds * f
                cash += proceeds - fee
                fees += fee
                closed.append(proceeds - fee - basis)
                trades.append({"ts": ts, "side": "sell", "price": o*(1-s), "qty": qty})
                qty = 0.0
            equity = cash + qty * close
            peak = max(peak, equity)
            dd = max(dd, (peak - equity) / peak * 100)
            curve.append({"ts": ts, "equity": equity})
            exposure.append(qty * close / equity)
        liquidation_fee = qty * rows[-1][4] * (1-s) * f
        liquidation_equity = cash + qty * rows[-1][4] * (1-s) - liquidation_fee
        outputs[arm] = {"marked_equity": cash + qty*rows[-1][4],
            "terminal_liquidation_equity": liquidation_equity,
            "net_after_terminal_liquidation": liquidation_equity-1000,
            "fees_including_terminal_liquidation": fees+liquidation_fee,
            "daily_close_max_drawdown_pct": dd, "closed_trades": len(closed),
            "net_winners": sum(x>0 for x in closed), "open_qty_before_terminal_liquidation": qty,
            "mean_close_exposure_fraction": sum(exposure)/len(exposure),
            "trades": trades, "equity": curve}
    return {"report_type": "exploratory_daily_signal_comparison",
        "reporting_currency": reporting_currency, "initial_cash": 1000, "entry_notional": 100,
        **({"initial_cash_usd": 1000, "entry_notional_usd": 100} if reporting_currency == "USD" else {}),
        "fee_bps": fee_bps, "slippage_bps": slippage_bps,
        "regime_entry": regime_entry,
        "two_close_entry": two_close_entry,
        "dataset_sha256": hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest(),
        "first_evaluated_ts": rows[200][0], "last_ts": rows[-1][0], "bars": len(rows),
        "limitations": [f"Not untouched data or campaign replay; SMA200 with {'regime-gated' if regime_entry else 'ungated'} entry and SMA-flat exit, not the full campaign risk/exit stack.",
            "Costs are declared scenarios, not verified account fees; no interest, funding or tax.",
            "No quantity rounding or minimum-order validation; historical archive provenance not independently verified.",
            f"100 {reporting_currency} entry limit, not continuous market-value exposure cap; no pyramiding or leverage.",
            "Drawdown sampled at daily closes; terminal liquidation is hypothetical, not a signal exit."],
        "arms": outputs}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive-db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    with sqlite3.connect(args.archive_db.resolve().as_uri()+"?mode=ro", uri=True) as con:
        rows = con.execute("SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange='coinbase' AND symbol='BTC/USD' AND timeframe='1d' ORDER BY ts_ms").fetchall()
    # Freeze all cost scenarios before seeing outcomes; no parameter search.
    results = [compare(rows, fee_bps=f, slippage_bps=s) for f,s in ((10.,5.),(20.,10.),(60.,10.))]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False)+"\n")
    for r in results:
        print(json.dumps({"fee_bps":r["fee_bps"],"slippage_bps":r["slippage_bps"],
            "arms": {k:{a:b for a,b in v.items() if a not in ("trades","equity")} for k,v in r["arms"].items()}}))


if __name__ == "__main__":
    main()
