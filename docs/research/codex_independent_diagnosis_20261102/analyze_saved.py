"""Aggregate saved result artifacts only; never import a simulator or read price archives."""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from statistics import fmean

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCES = {
    "es": "docs/research/es_exit_policy_matrix_20261007/es_exit_policy_matrix_20261007.json",
    "leader": "research/leader_target_results_corrected_20261012.json",
    "short_hold": "research/research_corrections_20261009/short_hold_corrected_v1.json",
    "dynamic_v1": "research/research_corrections_20261009/dynamic_corrected_v1.json",
    "dynamic_v2": "research/research_corrections_20261009/dynamic_corrected_v2.json",
    "band": "docs/research/candidate_band_20261013/band_result.json",
    "brake": "docs/research/crash_brake_20261013/crash_brake_result.json",
}


def closed_events(events):
    closed = [event for event in events if "net_pnl_usd" in event]
    values = [event["net_pnl_usd"] for event in closed]
    assert values and all(type(v) in (int, float) and math.isfinite(v) for v in values)
    wins = [v for v in values if v > 0]
    losses = [v for v in values if v < 0]
    frequencies = Counter((e["symbol"], e["entry_time"]) for e in closed)
    return {"closed": len(values), "wins": len(wins), "win_fraction": len(wins) / len(values),
            "mean_net_usd_per_event": fmean(values), "sum_net_usd_NOT_PORTFOLIO": math.fsum(values),
            "mean_winner_usd": fmean(wins) if wins else None,
            "mean_loser_usd": fmean(losses) if losses else None, "worst_usd": min(values),
            "gross_open_to_open_mean_pct": 100 * fmean(e["gross_return"] for e in closed),
            "unique_symbol_entry_times": len(frequencies),
            "duplicate_symbol_entry_exposures": sum(n - 1 for n in frequencies.values()),
            "target_exit_sum_usd": math.fsum(e["net_pnl_usd"] for e in closed if e["status"] == "TARGET_EXIT"),
            "timeout_exit_sum_usd": math.fsum(e["net_pnl_usd"] for e in closed if e["status"] == "TIMEOUT_EXIT")}


def summarize(data):
    es = data["es"]
    leader = []
    for arm in data["leader"]["runs"]:
        aggregate = closed_events(arm["combined"]["events"])
        assert aggregate["closed"] == arm["combined"]["closed_trades"]
        assert math.isclose(aggregate["sum_net_usd_NOT_PORTFOLIO"], arm["combined"]["sum_closed_net_usd_not_portfolio"], abs_tol=1e-7)
        leader.append({"pullback": arm["pullback"], "target": arm["target"], "max_days": arm["hold"],
                       **aggregate, "unresolved_entered": arm["combined"]["unresolved_entered_events"],
                       "mean_closed_plus_last_marks_usd": arm["combined"]["average_closed_plus_last_marks_usd"]})
    assert len(leader) == 8
    short = []
    rows = data["short_hold"]["results"]
    for period in ("last_60d", "prior_10m"):
        selected = {k.split("|")[1]: v for k, v in rows.items()
                    if k.split("|")[0] == period and k.split("|")[2:] == ["zero_fee", "outage"]}
        assert len(selected) == 14
        for strategy, zero in selected.items():
            paid = rows[f"{period}|{strategy}|primary_50bps|outage"]
            short.append({"period": period, "strategy": strategy,
                          "zero_fee_end_usd": zero["end_nav_usd"], "fee50bps_end_usd": paid["end_nav_usd"],
                          "zero_fee_closed": zero["closed_trades"], "fee50bps_closed": paid["closed_trades"],
                          "zero_fee_unknown_nav_hours": zero["unknown_nav_hours"],
                          "fee50bps_unknown_nav_hours": paid["unknown_nav_hours"],
                          "zero_fee_status": zero["status"], "fee50bps_status": paid["status"]})
    dynamic = dict(data["dynamic_v1"]["results"])
    dynamic.update(data["dynamic_v2"]["results"])
    selected_dynamic = {k: {field: v[field] for field in ("status", "end_nav_usd", "closed_trades", "unknown_nav_hours")}
                        for k, v in dynamic.items() if k.split("|")[2:] == ["primary_50bps", "outage"]}
    overlays = {}
    for source, treatment in (("band", "candidate_band_0.10"), ("brake", "braked")):
        overlays[source] = {"registered_verdict": data[source]["verdict"], "pairs": []}
        for fee, periods in data[source]["results"].items():
            for period, arms in periods.items():
                baseline, changed = arms["candidate"], arms[treatment]
                overlays[source]["pairs"].append({"fee_per_side": fee, "period": period,
                    "baseline_end_usd": baseline["end_usd"], "treatment_end_usd": changed["end_usd"],
                    "difference_end_usd": changed["end_usd"] - baseline["end_usd"],
                    "baseline_drawdown_pct": baseline["max_drawdown_pct"],
                    "treatment_drawdown_pct": changed["max_drawdown_pct"]})
    return {"bot_relation": "STANDALONE", "runtime_configuration_checked": "separate whitelisted snapshot; not applied to legacy studies",
            "evidence_scope": "saved-artifact arithmetic only; no new backtest, market data, hypothesis test or causal estimate",
            "es": {"assumptions": es["assumptions"], "window": es["window"], "cells": es["cells"]},
            "leader_eight_arms": leader, "short_hold_all_28_pairs": short,
            "dynamic_effective_saved_rows": selected_dynamic, "overlays": overlays}


def main():
    data, hashes = {}, {}
    for key, name in SOURCES.items():
        body = (ROOT / name).read_bytes()
        hashes[name] = hashlib.sha256(body).hexdigest()
        data[key] = json.loads(body)
    result = summarize(data)
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
    result["source_sha256"] = hashes
    result["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with (HERE / "saved_result_diagnosis.json").open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
    print(json.dumps({"sources": len(hashes), "leader_arms": len(result["leader_eight_arms"]),
                      "short_hold_pairs": len(result["short_hold_all_28_pairs"]), "new_simulations": 0}))


if __name__ == "__main__":
    main()
