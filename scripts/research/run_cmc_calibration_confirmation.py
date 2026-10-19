"""Resumable fixed synthetic confirmation; no market-data or scoring activation."""
import hashlib
import json
import time
from pathlib import Path
import numpy as np

from scripts.research.calibrate_cmc_synthetic import rate
from scripts.research.cmc_calibration_models import MODELS, MEANS, generate, stream_seed
from scripts.research.cmc_calibration_intervals import interval

ROOT = Path("research/research_corrections_20261009")
LOCK = ROOT/"cmc_development_method_lock_v2.json"
REQUIRED_SOURCES = {"scripts/research/run_cmc_calibration_development.py",
                    "scripts/research/cmc_calibration_models.py",
                    "scripts/research/cmc_calibration_intervals.py",
                    "docs/research/cmc_trending_log/calibration_power_contract_v2.md"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_lock(lock):
    if lock["method"] != "block28" or lock.get("confirmation_started") is not False:
        raise ValueError("invalid frozen method lock")
    if set(lock.get("source_hashes", {})) != REQUIRED_SOURCES:
        raise ValueError("mandatory source manifest required")
    if lock.get("numpy_version") != np.__version__:
        raise ValueError("NumPy runtime differs from lock")
    for path, digest in lock["source_hashes"].items():
        if sha(path) != digest:
            raise ValueError("source hash changed: "+path)


def validate_counts(part):
    values = [part.get(key) for key in ("positive", "unavailable", "refused")]
    if any(type(value) is not int or not 0 <= value <= 100 for value in values):
        raise ValueError("invalid checkpoint counts")
    positive, unavailable, refused = values
    if refused > unavailable or positive+unavailable > 100:
        raise ValueError("inconsistent checkpoint counts")


def evaluate_chunk(model, days, mean_index, start, size=100):
    positive = unavailable = refused = 0
    for trial in range(start, start+size):
        history = generate("confirmation", model, days, mean_index, trial)
        result = interval(history, "block28", stream_seed(
            "confirmation", model, days, mean_index, trial, "bootstrap"))
        if result["status"] == "DESCRIPTIVE":
            positive += result["p05"] > 0
        else:
            unavailable += 1
            refused += result["status"].startswith("REFUSED")
    return {"positive": positive, "unavailable": unavailable, "refused": refused}


def run(budget=600):
    lock = json.loads(LOCK.read_text())
    verify_lock(lock)
    hashes = {"lock": sha(LOCK), "runner": sha(__file__),
              "rate_helper": sha("scripts/research/calibrate_cmc_synthetic.py"),
              "numpy_version": np.__version__}
    directory = ROOT/"cmc_confirmation_v2"
    directory.mkdir(exist_ok=True)
    began = time.perf_counter()
    summaries = []
    for model in MODELS:
        for days in (90, 180, 365):
            for mean_index in range(4):
                counts = {"positive": 0, "unavailable": 0, "refused": 0}
                for start in range(0, 1000, 100):
                    path = directory/f"{model}_{days}_{mean_index}_{start}.json"
                    if path.exists():
                        part = json.loads(path.read_text())
                        if (part["hashes"] != hashes or part["model"] != model
                                or part["days"] != days or part["mean_index"] != mean_index
                                or part["start"] != start or part["trials"] != 100):
                            raise ValueError("mixed or invalid checkpoint: "+str(path))
                    else:
                        if time.perf_counter()-began >= budget:
                            return {"status": "BUDGET_CHECKPOINT", "elapsed_seconds": time.perf_counter()-began,
                                    "scoring_authorized": False}
                        result = evaluate_chunk(model, days, mean_index, start)
                        part = {"hashes": hashes, "model": model, "days": days,
                                "mean_index": mean_index, "start": start, "trials": 100, **result}
                        with path.open("x") as stream:
                            json.dump(part, stream, indent=2, allow_nan=False)
                    for key in counts:
                        validate_counts(part)
                        counts[key] += part[key]
                estimate = rate(counts["positive"], 1000)
                refusal_only = model in MODELS[6:]
                if refusal_only:
                    criterion = "REFUSAL_ONLY"
                    passed = counts["refused"] == 1000
                elif mean_index == 0:
                    criterion = "POINTWISE_NULL_TOLERANCE"
                    passed = estimate["wilson95"][1] <= .075 and counts["unavailable"] == 0
                elif MEANS[mean_index] == .005:
                    criterion = "TARGET_POWER"
                    passed = estimate["rate"] >= .8 and estimate["wilson95"][0] >= .75
                else:
                    criterion, passed = "DESCRIPTIVE_OTHER_EFFECT", None
                summaries.append({"model": model, "days": days, "mean": MEANS[mean_index],
                                  **counts, "positive_rate": estimate,
                                  "criterion": criterion, "criterion_met": passed})
                print(f"completed {model} days={days} mean_index={mean_index}", flush=True)
    candidates = [days for days in (90, 180, 365) if all(
        row["criterion_met"] is True for row in summaries if row["days"] == days
        and row["criterion"] != "DESCRIPTIVE_OTHER_EFFECT")]
    return {"status": "COMPLETE", "synthetic_only": True, "method": "block28",
            "trials": 108000, "hashes": hashes, "cells": summaries,
            "synthetic_candidate_days": min(candidates) if candidates else "NO_CERTIFIED_SAMPLE",
            "elapsed_seconds": time.perf_counter()-began, "scoring_authorized": False,
            "limits": ["pointwise_tolerance_not_error_rate_le_5_percent",
                       "no_real_market_sample_or_profitability_certification"]}


if __name__ == "__main__":
    result = run()
    if result["status"] == "COMPLETE":
        output = ROOT/"cmc_confirmation_summary_v2.json"
        with output.open("x") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k != "cells"}))
