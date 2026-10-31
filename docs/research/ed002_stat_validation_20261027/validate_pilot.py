"""One bounded synthetic method pilot, not a trading study or certification."""
import hashlib
import json
from pathlib import Path
import resource
import signal
import socket
import statistics
import subprocess
import sys
import time


def forbidden(*args, **kwargs):
    raise AssertionError("synthetic statistical pilot attempted external work")


for name in ("socket", "create_connection", "getaddrinfo"):
    setattr(socket, name, forbidden)
for name in ("Popen", "run", "call", "check_output", "check_call"):
    setattr(subprocess, name, forbidden)

import numpy as np
from services.backtest import paired_wealth_screen as method


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TRIALS, BUDGET_SECONDS, DATA_SEED = 32, 120, 20261128


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def daily_panel(values):
    return {arm: [{"day_end_ms": (i+1)*method.DAY, "return": float(values[i, j])}
                  for i in range(method.DAYS)] for j, arm in enumerate(method.ARMS)}


def wilson(count, n):
    z = statistics.NormalDist().inv_cdf(.975)
    p, d = count/n, 1+z*z/n
    center = (p+z*z/(2*n))/d
    half = z*((p*(1-p)/n+z*z/(4*n*n))**.5)/d
    return [max(0., center-half), min(1., center+half)]


def timeout(*args):
    raise TimeoutError("synthetic_pilot_120_second_limit")


def main():
    if (HERE/"ATTEMPT.json").exists() or (HERE/"result.json").exists():
        raise FileExistsError("preserve prior synthetic attempt; no automatic retry")
    sources = [Path(__file__), HERE/"decision.json", ROOT/"services/backtest/paired_wealth_screen.py"]
    sources = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    attempt = {"scope": "synthetic-only method pilot", "trials_per_null": TRIALS,
        "null_models": ["iid_exchangeable", "ar1_0.8_exchangeable"],
        "max_method_calls": 2*TRIALS+3, "resamples_per_call": method.REPEATS,
        "compute_deadline_seconds": BUDGET_SECONDS, "data_seed": DATA_SEED,
        "bootstrap_seed": method.SEED, "sources_sha256": sources,
        "network_or_market_inputs": False, "automatic_retry": False}
    with (HERE/"ATTEMPT.json").open("x") as f:
        json.dump(attempt, f, indent=2)
        f.write("\n")
    start = time.monotonic()
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(BUDGET_SECONDS)
    rng = np.random.Generator(np.random.PCG64(DATA_SEED))
    report = {"status": "INCOMPLETE", "statistical_validation": "INCOMPLETE",
        "coverage_certified": False, "experiment_pass": None, "nulls": {},
        "sensitivity_fixture": {}, "completed_method_calls": 0,
        "limits": ["32 trials per model cannot certify nominal familywise coverage or power",
                   "Wilson ranges describe independent synthetic trial frequencies only",
                   "null results concern these fixed exchangeable generators, not real-market validity",
                   "14/28-day sensitivities are descriptive and never replace primary seven-day blocks",
                   "no overhead double-charge in differences; overhead and economic filters are outside this method"]}
    try:
        for label, rho in (("iid_exchangeable", 0.), ("ar1_0.8_exchangeable", .8)):
            false_positives, counts = 0, dict.fromkeys(method.FAMILIES, 0)
            for trial in range(TRIALS):
                innovations = rng.normal(size=(method.DAYS+1024, 5))
                process = np.zeros_like(innovations)
                for i in range(1, len(process)):
                    process[i] = rho*process[i-1] + (1-rho*rho)**.5*innovations[i]
                x = process[-method.DAYS:]
                log_returns = .01*x[:, :1] + .005*x[:, 1:]
                values = np.zeros((method.DAYS, len(method.ARMS)))
                values[:, :4] = np.expm1(log_returns)
                values[:, 5] = np.expm1(.01*x[:, 0])
                values[:, 6] = .5*values[:, 5]
                outcome = method.paired_wealth_screen(daily_panel(values), initial_cash=1000)
                report["completed_method_calls"] += 1
                if outcome["computation_status"] != "COMPLETE":
                    raise ValueError("incomplete_null_computation")
                flags = [outcome["contrasts"][name]["lower_bound_exceeds_zero"] for name in method.FAMILIES]
                false_positives += any(flags)
                for name, flag in zip(method.FAMILIES, flags):
                    counts[name] += flag
            interval = wilson(false_positives, TRIALS)
            report["nulls"][label] = {"trials": TRIALS, "rho": rho, "burn_in": 1024,
                "familywise_false_positive_count": false_positives,
                "familywise_rate": false_positives/TRIALS, "wilson_95_range": interval,
                "individual_counts": counts, "range_lower_above_nominal_0.05": interval[0] > .05,
                "null_basis": "three families and incumbent have identical marginal path laws; no expected wealth advantage"}
        values = np.zeros((method.DAYS, len(method.ARMS)))
        values[:, :3] = .001
        for block in method.BLOCKS:
            result = method.paired_wealth_screen(daily_panel(values), initial_cash=1000, block_days=block)
            report["completed_method_calls"] += 1
            report["sensitivity_fixture"][str(block)] = result
        report["status"] = "COMPLETE"
    except (TimeoutError, ValueError, FloatingPointError) as error:
        report["failure"] = str(error)
    finally:
        signal.alarm(0)
    report["elapsed_seconds"] = round(time.monotonic()-start, 6)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["peak_rss_bytes"] = rss if sys.platform == "darwin" else rss*1024
    report["numpy_version"] = np.__version__
    report["sources_sha256"] = sources
    with (HERE/"result.json").open("x") as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({k: report[k] for k in ("status", "statistical_validation",
        "completed_method_calls", "elapsed_seconds", "peak_rss_bytes", "nulls")}))
    if report["status"] != "COMPLETE":
        raise RuntimeError("synthetic_pilot_incomplete_see_preserved_result")


if __name__ == "__main__":
    main()
