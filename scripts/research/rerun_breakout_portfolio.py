"""Continuous frozen breakout portfolio diagnostic, not promotion evidence."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

from scripts.research.rerun_frozen_breakout import load_frozen_features


def portfolio(opens, closes, present, events, lo, end, fee=.005, slots=5, hold=72,
              outage_policy=False, market_index=None):
    """Only observed current prices; no future-completeness filter on entries."""
    cash, positions, curve, fills = 1000.0, {}, [], []
    unpriced_hours, deferred_exit_hours = 0, 0
    refusals = collections.Counter()
    signals = collections.defaultdict(list)
    for signal, coin in events:
        signals[signal + 1].append(coin)

    def price(coin, hour, opening):
        if not present[coin][hour]:
            return None
        value = float((opens if opening else closes)[coin][hour])
        return value if 0 < value < float("inf") else None

    def incomplete(hour, coin, reason):
        return {"status": "INCOMPLETE", "hour": hour, "coin_index": coin,
                "reason": reason, "cash": cash, "positions": positions,
                "curve": curve, "fills": fills, "refusals": dict(refusals)}

    for hour in range(lo, end + 1):
        for coin, position in list(positions.items()):
            if hour >= position["exit"] or hour == end:
                opening = price(coin, hour, True)
                if opening is None:
                    if outage_policy and hour != end:
                        deferred_exit_hours += 1
                        continue
                    return incomplete(hour, coin, "missing_exit_open")
                received = position["quantity"] * opening * .999 * (1 - fee)
                cash += received
                fills.append({"hour": hour, "coin_index": coin, "side": "sell",
                              "quantity": position["quantity"], "cash_change": received,
                              "reference_open": opening, "terminal": hour == end,
                              "delay_hours": max(0, hour - position["exit"])})
                del positions[coin]
        if hour == end:
            break
        for coin in signals.get(hour, []):
            if outage_policy and (
                (market_index is not None and price(market_index, hour, True) is None)
                or any(price(held, hour, True) is None or price(held, hour - 1, False) is None
                       for held in positions)
            ):
                refusals["outage_entry_block"] += 1
                continue
            if coin in positions or len(positions) >= slots:
                refusals["held_or_slots_full"] += 1
                continue
            opening = price(coin, hour, True)
            if opening is None:
                refusals["missing_entry_open"] += 1
                continue
            equity = cash
            for held, position in positions.items():
                mark = price(held, hour - 1, False)
                if mark is None:
                    return incomplete(hour, held, "missing_entry_sizing_mark")
                equity += position["quantity"] * mark
            allocation = min(cash, equity / slots)
            if allocation < 1:
                refusals["insufficient_cash"] += 1
                continue
            quantity = allocation / (opening * 1.001 * (1 + fee))
            cash -= allocation
            positions[coin] = {"quantity": quantity, "exit": hour + hold}
            fills.append({"hour": hour, "coin_index": coin, "side": "buy",
                          "quantity": quantity, "cash_change": -allocation,
                          "reference_open": opening})
        equity = cash
        for coin, position in positions.items():
            mark = price(coin, hour, False)
            if mark is None:
                if outage_policy:
                    equity = None
                    unpriced_hours += 1
                    break
                return incomplete(hour, coin, "missing_held_valuation")
            equity += position["quantity"] * mark
        curve.append({"hour": hour, "equity": equity, "cash": cash,
                      "positions": len(positions)})
    return {"status": "COMPLETE_WITH_UNPRICED_INTERVALS" if unpriced_hours else "COMPLETE_DIAGNOSTIC", "terminal_cash": cash,
            "net_return": cash / 1000 - 1, "curve": curve, "fills": fills,
            "refusals": dict(refusals), "terminal_hour": end,
            "unpriced_hours": unpriced_hours, "deferred_exit_position_hours": deferred_exit_hours,
            "drawdown_verified": not bool(unpriced_hours)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--outage-policy", action="store_true")
    args = parser.parse_args()
    ns = load_frozen_features(args.input_root)
    results = []
    for mult in (3, 2):
        events = ns["events"](mult)
        for fee in (.005, .006, .012):
            result = portfolio(ns["O"], ns["Cl"], ns["PRES"], events,
                               721, ns["NH"] - 1, fee,
                               outage_policy=args.outage_policy, market_index=ns["bi"])
            results.append({"volume_multiple": mult, "fee_bps": fee * 10000, **result})
    files = sorted(p for d in ("cb/h1", "cb2/h1") for p in (args.input_root / d).glob("*.json"))
    output = {"artifact_type": "frozen_breakout_continuous_portfolio_v1",
              "not_promotion_evidence": True, "not_fresh_holdout": True,
              "initial_cash": 1000, "slots": 5, "hold_hours": 72,
              "segment_split_hour": (ns["SPLIT"] - ns["START"]) // 3600,
              "carry_forward": True,
              "price_gaps": "retain holdings; block entries; defer exits; null valuations" if args.outage_policy else "stop incomplete, no imputed prices",
              "execution_policy_amendment": args.outage_policy,
              "start_timestamp": ns["START"], "coins": ns["coins"],
              "source": Path(__file__).read_text(),
              "feature_source": (Path(__file__).with_name("rerun_frozen_breakout.py")).read_text(),
              "input_sha256": {str(p.relative_to(args.input_root)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in files}, "results": results}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(output, stream, allow_nan=False)
    print(json.dumps({"file": str(args.out), "statuses": [r["status"] for r in results]}))


if __name__ == "__main__":
    main()
