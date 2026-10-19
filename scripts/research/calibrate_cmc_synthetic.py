"""Bounded synthetic null calibration, not a scoring policy or market study."""
import argparse
import hashlib
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

from scripts.research.cmc_statistics import summarize


def null_returns(days, seed, mode):
    rng = random.Random(seed)
    shocks = [rng.gauss(0, .03) for _ in range(days+6)]
    if mode == "iid":
        return shocks[:days]
    if mode == "overlap7":
        return [sum(shocks[i:i+7])/7 for i in range(days)]
    if mode == "persistent":
        state = rng.gauss(0, .03/math.sqrt(1-.85**2))
        values = []
        for shock in shocks[:days]:
            state = .85*state+shock
            values.append(state)
        return values
    raise ValueError("unknown synthetic mode")


def rate(count, total):
    p, z = count/total, 1.96
    denom = 1+z*z/total
    center = (p+z*z/(2*total))/denom
    width = z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return {"count": count, "trials": total, "rate": p,
            "wilson95": [center-width, center+width]}


def run(trials=30, repeats=100):
    if trials < 2 or repeats < 100:
        raise ValueError("at least2 trials and100 bootstrap replicates required")
    results = []
    for days in (60, 180):
        dates = [(date(2026, 1, 1)+timedelta(days=i)).isoformat() for i in range(days)]
        for mode in ("iid", "overlap7", "persistent"):
            positive = {name: 0 for name in ("entry_day", "7", "14", "28", "all_intervals")}
            unavailable = dict.fromkeys(positive, 0)
            for trial in range(trials):
                rows = [{"status": "DIAGNOSTIC", "horizon_days": 7,
                         "utc_day": day, "excess_return": value}
                        for day, value in zip(dates, null_returns(days, 20261009+trial, mode))]
                report = summarize(rows, dates, True, repeats=repeats, seed=30261009+trial)
                bands = {"entry_day": report["registered_entry_day_bootstrap"],
                         **report["serial_dependence_sensitivities_not_replacement_gate"]}
                for name, band in bands.items():
                    if band["status"] != "DESCRIPTIVE":
                        unavailable[name] += 1
                    elif band["p05"] > 0:
                        positive[name] += 1
                if all(b["status"] == "DESCRIPTIVE" for b in bands.values()):
                    positive["all_intervals"] += all(b["p05"] > 0 for b in bands.values())
                else:
                    unavailable["all_intervals"] += 1
            results.append({"days": days, "mode": mode,
                            "false_positive": {k: rate(v, trials) for k,v in positive.items()},
                            "unavailable_intervals": unavailable})
    return {"artifact_type": "synthetic_null_calibration", "synthetic_only": True,
            "scoring_authorized": False, "trials_per_cell": trials,
            "bootstrap_repeats": repeats, "results": results,
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "statistics_sha256": hashlib.sha256(Path("scripts/research/cmc_statistics.py").read_bytes()).hexdigest(),
            "limits": ["pilot_not_sample_size_certification", "no_alternative_power_test",
                       "one_event_per_day_no_missingness_or_regime_shift",
                       "no_market_data_access_or_frozen_rule_change"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with args.out.open("x") as stream:
        json.dump(run(), stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
