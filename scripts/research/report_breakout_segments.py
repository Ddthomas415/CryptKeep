"""Descriptive carry-forward segment attribution, never fresh holdout proof."""
import argparse
import hashlib
import json
from pathlib import Path


def attribute(curve, split, terminal, initial=1000):
    boundary = next((r["equity"] for r in curve if r["hour"] == split - 1), None)
    if boundary is None or boundary <= 0:
        return {"status": "INCOMPLETE", "reason": "missing_pre_split_valuation"}
    return {"status": "DESCRIPTIVE", "boundary_hour": split - 1,
            "boundary_equity": boundary, "earlier_dollar_change": boundary - initial,
            "later_dollar_change": terminal - boundary,
            "later_return_on_carried_equity": terminal / boundary - 1,
            "terminal_cash": terminal}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portfolio", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    p_raw, b_raw = args.portfolio.read_bytes(), args.comparison.read_bytes()
    portfolio, comparison = json.loads(p_raw), json.loads(b_raw)
    if hashlib.sha256(p_raw).hexdigest() != comparison["portfolio_sha256"]:
        raise ValueError("parent artifact mismatch")
    split = portfolio["segment_split_hour"]
    benchmarks = {(r["volume_multiple"], r["fee_bps"]): r for r in comparison["results"]}
    results = []
    for row in portfolio["results"]:
        pair = benchmarks[(row["volume_multiple"], row["fee_bps"])]
        strategy = attribute(row["curve"], split, row["terminal_cash"])
        btc = attribute(pair["btc"]["curve"], split, pair["btc"]["terminal_cash"])
        results.append({"volume_multiple": row["volume_multiple"], "fee_bps": row["fee_bps"],
                        "strategy": strategy, "btc": btc,
                        "later_dollar_change_gap": strategy["later_dollar_change"] - btc["later_dollar_change"]
                        if strategy["status"] == btc["status"] == "DESCRIPTIVE" else None})
    output = {"artifact_type": "carry_forward_segment_attribution_v1",
              "not_fresh_holdout": True, "not_promotion_evidence": True,
              "boundary_basis": "observed close immediately before split; no trades or reset",
              "terminal_basis": "net liquidation at common final open",
              "limitation": "different carried capital; dollar gap is not equal-capital segment performance; no CI or gap drawdown",
              "portfolio_sha256": hashlib.sha256(p_raw).hexdigest(),
              "comparison_sha256": hashlib.sha256(b_raw).hexdigest(),
              "source": Path(__file__).read_text(), "results": results}
    with args.out.open("x") as stream:
        json.dump(output, stream, allow_nan=False)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
