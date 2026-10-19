"""Bounded public-data signal experiment; no intents, fills or account access."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.strategies.presets import PRESETS
from services.strategies.strategy_registry import compute_signal

BASE = "https://api.exchange.coinbase.com/products/BTC-USD"


def fetch(endpoint):
    started = time.time_ns()
    result = subprocess.run(["curl", "--silent", "--show-error", "--fail",
                             "--max-time", "5", BASE + endpoint],
                            capture_output=True, text=True, timeout=7, check=True)
    return {"request_ns": started, "received_ns": time.time_ns(),
            "mono_ns": time.monotonic_ns(), "payload": json.loads(result.stdout)}


def closed_bars(payload, now_sec):
    rows = sorted([[int(r[0])*1000, float(r[3]), float(r[2]), float(r[1]),
                    float(r[4]), float(r[5])] for r in payload
                   if int(r[0])+300 <= now_sec])
    if len(rows) < 40:
        raise ValueError("insufficient_closed_bars")
    for i, (ts, op, hi, lo, cl, vol) in enumerate(rows):
        if not all(math.isfinite(v) for v in (op, hi, lo, cl, vol)):
            raise ValueError("nonfinite_bar")
        if not 0 < lo <= min(op, cl) <= max(op, cl) <= hi or vol < 0:
            raise ValueError("invalid_bar")
        if i and ts-rows[i-1][0] != 300000:
            raise ValueError("bar_gap")
    if now_sec-(rows[-1][0]/1000+300) > 330:
        raise ValueError("stale_closed_bar")
    return rows


def quote(packet):
    bid, ask = float(packet["payload"]["bid"]), float(packet["payload"]["ask"])
    if not (math.isfinite(bid) and math.isfinite(ask) and 0 < bid <= ask):
        raise ValueError("invalid_quote")
    return {"bid": bid, "ask": ask, "mono_ns": packet["mono_ns"],
            "received_ns": packet["received_ns"]}


def label(entry, later):
    return {"gross_mid_bps": (((later["bid"]+later["ask"])/
                               (entry["bid"]+entry["ask"]))-1)*10000,
            "quote_cross_return_bps": (later["bid"]/entry["ask"]-1)*10000,
            "break_even_equal_fee_bps_per_side":
                (later["bid"]-entry["ask"])/(later["bid"]+entry["ask"])*10000,
            "meaning": "quoted_price_counterfactual_not_fill; excludes_slippage_and_impact"}


def run(output, duration=3600):
    if not 60 <= duration <= 3600:
        raise ValueError("duration must be 60..3600 seconds")
    output.mkdir(parents=True, exist_ok=False)
    strategy = deepcopy(PRESETS["breakout_default"]["strategy"])
    contract = {"session_id": uuid.uuid4().hex, "duration_sec": duration,
                "strategy": strategy, "venue": "coinbase", "symbol": "BTC/USD",
                "timeframe_sec": 300, "quote_poll_sec": 5, "horizons_sec": [30, 60],
                "lateness_tolerance_sec": 10, "max_consecutive_errors": 3,
                "scope": "signal_only_not_campaign_admission_or_complete_strategy",
                "account_fees": "UNKNOWN", "trade_size": "not_modelled",
                "max_signal_delay_from_bar_close_sec": 60,
                "decision": "descriptive_or_insufficient_only_no_promotion",
                "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (output/"contract.json").write_text(json.dumps(contract, indent=2))
    deadline = time.monotonic()+duration
    next_candles, last_bar = 0, None
    pending, labels, signals = [], [], []
    errors, consecutive, stop_reason = [], 0, "duration_complete"
    with (output/"raw.jsonl").open("x") as raw:
        while time.monotonic() < deadline:
            try:
                signal = None
                if time.time() >= next_candles:
                    packet = fetch("/candles?granularity=300")
                    raw.write(json.dumps({"kind": "candles", **packet})+"\n")
                    raw.flush()
                    bars = closed_bars(packet["payload"], packet["received_ns"]/1e9)
                    next_candles = (int(time.time())//300+1)*300+2
                    if (bars[-1][0] != last_bar and
                            packet["received_ns"]/1e9-(bars[-1][0]/1000+300) <= 60):
                        last_bar = bars[-1][0]
                        signal = compute_signal(cfg={"strategy": strategy}, symbol="BTC/USD", ohlcv=bars)
                        signal = {"bar_ms": last_bar, "observed_ns": time.time_ns(), **signal}
                        signals.append(signal)
                        raw.write(json.dumps({"kind": "signal", **signal})+"\n")
                        raw.flush()
                packet = fetch("/ticker")
                raw.write(json.dumps({"kind": "quote", **packet})+"\n")
                raw.flush()
                q = quote(packet)
                if signal and signal.get("ok") is True and signal.get("action") == "buy":
                    pending.extend({"entry": q, "bar_ms": last_bar, "horizon": h}
                                   for h in contract["horizons_sec"])
                for item in pending[:]:
                    elapsed = (q["mono_ns"]-item["entry"]["mono_ns"])/1e9
                    if elapsed >= item["horizon"]:
                        available = elapsed <= item["horizon"]+contract["lateness_tolerance_sec"]
                        labels.append({"bar_ms": item["bar_ms"], "horizon_sec": item["horizon"],
                                       "elapsed_sec": elapsed,
                                       "result": label(item["entry"], q) if available else None})
                        pending.remove(item)
                consecutive = 0
            except Exception as exc:
                consecutive += 1
                errors.append({"observed_ns": time.time_ns(), "type": type(exc).__name__})
                if consecutive >= 3:
                    stop_reason = "data_blocked"
                    break
            report = {"status": "running", "signals": signals, "labels": labels,
                      "errors": errors, "pending_labels": len(pending), "profitability": "NOT_EVALUATED"}
            (output/"status.json").write_text(json.dumps(report, indent=2))
            time.sleep(max(0, min(5, deadline-time.monotonic())))
    report = {"status": stop_reason, "signals": signals, "labels": labels, "errors": errors,
              "pending_labels": len(pending), "profitability": "NOT_EVALUATED",
              "outcome": "DESCRIPTIVE_ONLY" if any(x["result"] for x in labels) else "INSUFFICIENT_EVIDENCE"}
    (output/"result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"output": str(output), **report}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--duration", type=int, default=3600)
    args = parser.parse_args()
    run(args.output, args.duration)
