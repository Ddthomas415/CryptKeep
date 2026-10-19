"""Fixed contract-v2 development screen; no confirmation or market data."""
import hashlib
import json
import time
from pathlib import Path

from scripts.research.cmc_calibration_models import MODELS, generate, stream_seed
from scripts.research.cmc_calibration_intervals import METHODS, interval


def select_method(cells):
    eligible = [method for method in METHODS if all(
        cell["methods"][method]["available"] > 0 for cell in cells)]
    if not eligible:
        return "NO_METHOD_LOCKED"
    preference = {"block56": 0, "block28": 1, "entry_day": 2}
    return min(eligible, key=lambda method: (
        max(cell["methods"][method]["positive"] for cell in cells), preference[method]))


def run():
    started = time.perf_counter()
    cells = []
    for model in MODELS[:6]:
        for days in (90, 365):
            counts = {m: {"available": 0, "positive": 0, "unavailable": 0} for m in METHODS}
            for trial in range(10):
                if time.perf_counter()-started > 600:
                    raise TimeoutError("development compute budget exhausted")
                history = generate("development", model, days, 0, trial)
                seed = stream_seed("development", model, days, 0, trial, "bootstrap")
                for method in METHODS:
                    result = interval(history, method, seed)
                    if result["status"] == "DESCRIPTIVE":
                        counts[method]["available"] += 1
                        counts[method]["positive"] += result["p05"] > 0
                    else:
                        counts[method]["unavailable"] += 1
            cells.append({"model": model, "days": days, "methods": counts})
    paths = ["scripts/research/run_cmc_calibration_development.py",
             "scripts/research/cmc_calibration_models.py",
             "scripts/research/cmc_calibration_intervals.py",
             "docs/research/cmc_trending_log/calibration_power_contract_v2.md"]
    return {"artifact_type": "synthetic_development_method_lock", "synthetic_only": True,
            "method": select_method(cells), "cells": cells, "method_history_evaluations": 360,
            "elapsed_seconds": time.perf_counter()-started,
            "source_hashes": {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths},
            "scoring_authorized": False, "confirmation_started": False,
            "limits": ["development_selection_not_confirmation", "no_market_sample_certified"]}


if __name__ == "__main__":
    output = Path("research/research_corrections_20261009/cmc_development_method_lock_v1.json")
    result = run()
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"method": result["method"], "elapsed_seconds": result["elapsed_seconds"]}))
