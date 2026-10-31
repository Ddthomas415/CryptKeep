"""One authorized SB-1 development attempt; no audit or market-data mode."""
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import socket
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOMAIN = "ED002-SB1-development-20261027"
CASES = (("iid_gaussian", 0.), ("ar1_0.5", .5), ("ar1_0.8", .8),
         ("ar1_0.95", .95), ("ar1_-0.5", -.5), ("volatility_two_state", None))
TRIALS, BURN, COMPUTE_SECONDS, JOURNAL_LIMIT = 16, 1024, 90, 12*1024*1024
_PHASE = "not_running"


def phase_timeout(*args):
    raise TimeoutError("development_timeout:"+_PHASE)


def begin_phase(label, seconds):
    global _PHASE
    _PHASE = label
    signal.signal(signal.SIGALRM, phase_timeout)
    signal.alarm(seconds)


def forbidden(*args, **kwargs):
    raise AssertionError("development attempted network or child process")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_hex(identity, case, trial, stream):
    return hashlib.sha256(f"{DOMAIN}|{identity}|{case}|{trial}|{stream}".encode()).hexdigest()


def gaussian_factors(innovations, initial, rho):
    import numpy as np
    if (not -1 < rho < 1 or innovations.ndim != 2 or initial.shape != innovations.shape[1:]
            or not np.isfinite(innovations).all() or not np.isfinite(initial).all()):
        raise ValueError("invalid_stationary_factor_inputs")
    result = np.empty_like(innovations)
    result[0] = initial
    for i in range(1, len(result)):
        result[i] = rho*result[i-1]+math.sqrt(1-rho*rho)*innovations[i]
    return result


def volatility_scales(uniforms, initial):
    import numpy as np
    if initial not in (0, 1) or uniforms.ndim != 1 or not np.isfinite(uniforms).all() or np.any((uniforms < 0) | (uniforms >= 1)):
        raise ValueError("invalid_volatility_inputs")
    states = np.empty(len(uniforms)+1, dtype=np.int64)
    states[0] = initial
    states[1:] = (initial+np.cumsum(uniforms >= .95)) % 2
    return np.where(states == 0, .5, 2.)


def null_returns(factors):
    import numpy as np
    if factors.shape != (182, 5) or not np.isfinite(factors).all():
        raise ValueError("explicit182by5null_factors_required")
    values = np.zeros((182, 7))
    values[:, :4] = np.expm1(.01*factors[:, :1]+.005*factors[:, 1:])
    values[:, 5] = np.expm1(.01*factors[:, 0])
    values[:, 6] = .5*values[:, 5]
    return values


def summarize(records, case, interrupted=None):
    selected = [r for r in records if r["case"] == case]
    complete = [r for r in selected if r["method_result"]["computation_status"] == "COMPLETE"]
    positives = sum(any(c["lower_bound_exceeds_zero"] for c in r["method_result"]["contrasts"].values()) for r in complete)
    reasons = {}
    for record in selected:
        if record["method_result"]["computation_status"] != "COMPLETE":
            reason = record["method_result"].get("reason", "unknown_failure")
            reasons[reason] = reasons.get(reason, 0)+1
    interrupted_count = int(interrupted is not None and interrupted["case"] == case)
    return {"planned_trials": TRIALS, "completed_trials": len(selected), "computable_trials": len(complete),
        "abstentions_or_failures": len(selected)-len(complete), "interrupted_trials": interrupted_count,
        "unattempted_trials": TRIALS-len(selected)-interrupted_count,
        "availability": len(complete)/len(selected) if selected else None,
        "familywise_positive_count": positives,
        "unconditional_positive_rate": positives/len(selected) if selected else None,
        "conditional_positive_rate": positives/len(complete) if complete else None,
        "reasons": reasons, "qualification": "DEVELOPMENT_DIAGNOSTIC_NOT_AUDIT_OR_ERROR_CERTIFICATION"}


def main():
    if len(sys.argv) != 1:
        raise ValueError("no_arguments_or_audit_mode_supported")
    if any((HERE/name).exists() for name in ("ATTEMPT.json", "trials.jsonl", "result.json")):
        raise FileExistsError("existing_development_attempt_preserved_no_retry")
    for name in ("socket", "create_connection", "getaddrinfo"):
        setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        setattr(subprocess, name, forbidden)
    begin_phase("imports", 15)
    import_start = time.monotonic()
    import numpy as np
    from services.backtest import sb1_prototype as method
    import_seconds = time.monotonic()-import_start
    signal.alarm(0)
    begin_phase("preflight", 15)
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"):
        if os.environ.get(key) != "1":
            raise ValueError("explicit_single_thread_environment_required")
    submitted = json.loads((ROOT/"docs/research/ed002_sb1_prototype_bindings_20261027.json").read_text())
    if not all(sha(ROOT/p) == h for p, h in submitted["inputs_sha256"].items()):
        raise ValueError("accepted_prototype_input_changed")
    authorization = json.loads((HERE/"authorization.json").read_text())
    if sha(ROOT/"services/backtest/sb1_prototype.py") != authorization["accepted_prototype_sha256"]:
        raise ValueError("human_accepted_prototype_hash_mismatch")
    if (method.DAYS, method.REPEATS, method.BATCH) != (182, 20000, 256):
        raise ValueError("fixed_method_constants_changed")
    sources = {str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), HERE/"authorization.json",
        ROOT/"services/backtest/sb1_prototype.py", ROOT/"docs/research/ed002_stat_revision_plan_20261027.md")}
    identity = hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    attempt = {"stage": "DEVELOPMENT_ONLY", "identity": identity, "domain": DOMAIN,
        "cases": [c for c, _ in CASES], "trials_each": TRIALS, "max_method_calls": 96,
        "compute_limit_seconds": COMPUTE_SECONDS, "import_limit_seconds": 15,
        "preflight_limit_seconds": 15, "final_receipt_limit_seconds": 5,
        "import_elapsed_seconds": import_seconds, "journal_byte_limit": JOURNAL_LIMIT,
        "sources_sha256": sources, "numpy_version": np.__version__,
        "audit_or_market_run": False, "retry": False}
    with (HERE/"ATTEMPT.json").open("x") as f:
        json.dump(attempt, f, indent=2)
        f.write("\n")
    signal.alarm(0)
    records, journal_bytes, calls_started, active = [], 0, 0, None
    report = {"status": "INCOMPLETE", "statistical_validation": "INCOMPLETE",
        "coverage_certified": False, "experiment_pass": None, "audit_run": False,
        "identity": identity, "sources_sha256": sources}
    start = time.monotonic()
    begin_phase("development_compute", COMPUTE_SECONDS)
    try:
        with (HERE/"trials.jsonl").open("x") as journal:
            for case, rho in CASES:
                for trial in range(TRIALS):
                    data_seed, draw_seed = seed_hex(identity, case, trial, "data"), seed_hex(identity, case, trial, "draws")
                    active = {"case": case, "trial": trial, "data_seed_hex": data_seed,
                              "draw_seed_hex": draw_seed, "method_call_started": False}
                    rng = np.random.Generator(np.random.PCG64(int(data_seed, 16)))
                    size = method.DAYS+BURN
                    innovations = rng.standard_normal((size, 5))
                    if rho is None:
                        initial = int(rng.integers(0, 2))
                        factors = innovations*volatility_scales(rng.random(size-1), initial)[:, None]
                    else:
                        factors = gaussian_factors(innovations, rng.standard_normal(5), rho)
                    values = null_returns(factors[-method.DAYS:])
                    panel = {arm: [{"day_end_ms": (i+1)*method.DAY, "return": float(values[i, j])}
                                   for i in range(method.DAYS)] for j, arm in enumerate(method.ARMS)}
                    draw_rng = np.random.Generator(np.random.PCG64(int(draw_seed, 16)))
                    starts = draw_rng.integers(0, method.DAYS, size=(method.REPEATS, method.DAYS), dtype=np.int64)
                    uniforms = draw_rng.random(starts.shape)
                    active["method_call_started"] = True
                    calls_started += 1
                    result = method.sb1_screen(panel, initial_cash=1000, starts=starts, uniforms=uniforms)
                    record = {"case": case, "trial": trial, "data_seed_hex": data_seed,
                        "draw_seed_hex": draw_seed, "null_returns": values.tolist(),
                        "returns_sha256": hashlib.sha256(memoryview(values).cast("B")).hexdigest(),
                        "draws_sha256": {"starts": hashlib.sha256(memoryview(starts).cast("B")).hexdigest(),
                                         "uniforms": hashlib.sha256(memoryview(uniforms).cast("B")).hexdigest()},
                        "method_result": result}
                    encoded = json.dumps(record, separators=(",", ":"), allow_nan=False)+"\n"
                    journal_bytes += len(encoded.encode())
                    if journal_bytes > JOURNAL_LIMIT:
                        raise RuntimeError("development_journal_byte_limit")
                    journal.write(encoded)
                    journal.flush()
                    records.append(record)
                    active = None
        report["status"] = "COMPLETE"
    except (TimeoutError, ValueError, FloatingPointError, OverflowError, RuntimeError) as error:
        report["failure"] = str(error)
    finally:
        signal.alarm(0)
    report["compute_elapsed_seconds"] = round(time.monotonic()-start, 6)
    begin_phase("final_receipt", 5)
    report["completed_method_calls"] = len(records)
    report["method_calls_started"] = calls_started
    report["interrupted_trial"] = active
    report["cases"] = {case: summarize(records, case, active) for case, _ in CASES}
    report["trials_sha256"] = sha(HERE/"trials.jsonl")
    report["journal_bytes"] = journal_bytes
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["peak_rss_bytes"] = rss if sys.platform == "darwin" else rss*1024
    with (HERE/"result.json").open("x") as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write("\n")
    signal.alarm(0)
    print(json.dumps({k: report[k] for k in ("status", "completed_method_calls",
        "compute_elapsed_seconds", "peak_rss_bytes", "cases")}))
    if report["status"] != "COMPLETE":
        raise RuntimeError("development_incomplete_preserved_no_retry")


if __name__ == "__main__":
    main()
