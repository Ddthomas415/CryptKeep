"""Cost-matched frozen portfolio/BTC comparison, not validation evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts.research.rerun_frozen_breakout import load_frozen_features


def benchmark(opens, closes, present, lo, end, fee, initial=1000):
    def observed(values, hour):
        value = float(values[hour])
        return bool(present[hour]) and math.isfinite(value) and value > 0

    if not observed(opens, lo) or not observed(opens, end):
        return {"status": "INCOMPLETE", "terminal_cash": None}
    quantity = initial / (float(opens[lo]) * 1.001 * (1 + fee))
    terminal = quantity * float(opens[end]) * .999 * (1 - fee)
    curve = [{"hour": h, "equity": quantity * float(closes[h])
              if observed(closes, h) else None} for h in range(lo, end)]
    missing = sum(row["equity"] is None for row in curve)
    return {"status": "COMPLETE_WITH_UNPRICED_INTERVALS" if missing else "COMPLETE_DIAGNOSTIC",
            "entry_hour": lo, "terminal_hour": end, "quantity": quantity,
            "terminal_cash": terminal, "net_return": terminal / initial - 1,
            "unpriced_hours": missing, "curve": curve,
            "drawdown_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--portfolio", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.portfolio.read_bytes()
    original = json.loads(raw)
    for relative, expected in original["input_sha256"].items():
        if hashlib.sha256((args.input_root / relative).read_bytes()).hexdigest() != expected:
            raise ValueError("input hash mismatch: " + relative)
    ns = load_frozen_features(args.input_root)
    if ns["START"] != original["start_timestamp"] or ns["coins"] != original["coins"]:
        raise ValueError("feature alignment mismatch")
    results = []
    for row in original["results"]:
        if not row["status"].startswith("COMPLETE"):
            raise ValueError("portfolio endpoint incomplete")
        lo, end = row["curve"][0]["hour"], row["terminal_hour"]
        btc = benchmark(ns["O"][ns["bi"]], ns["Cl"][ns["bi"]],
                        ns["PRES"][ns["bi"]], lo, end, row["fee_bps"] / 10000)
        results.append({"volume_multiple": row["volume_multiple"], "fee_bps": row["fee_bps"],
                        "entry_timestamp": ns["START"] + lo * 3600,
                        "terminal_timestamp": ns["START"] + end * 3600,
                        "strategy_terminal_cash": row["terminal_cash"], "btc": btc,
                        "terminal_dollar_gap": None if btc["terminal_cash"] is None
                        else row["terminal_cash"] - btc["terminal_cash"]})
    output = {"artifact_type": "cost_matched_btc_comparison_v1", "not_fresh_holdout": True,
              "not_promotion_evidence": True, "no_confidence_intervals": True,
              "drawdown_not_evaluated": True, "initial_cash": 1000,
              "slippage_each_side": .001, "fees_each_side": True,
              "portfolio_sha256": hashlib.sha256(raw).hexdigest(),
              "input_sha256": original["input_sha256"],
              "source": Path(__file__).read_text(), "results": results}
    with args.out.open("x") as stream:
        json.dump(output, stream, allow_nan=False)
    print(json.dumps([{k: r[k] for k in ("volume_multiple", "fee_bps", "terminal_dollar_gap")}
                      for r in results]))


if __name__ == "__main__":
    main()
