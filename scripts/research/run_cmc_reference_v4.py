"""Bounded synthetic reference generation only; no market access or scoring."""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path

from scripts.research import cmc_calibration_v3 as models

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs/research/cmc_trending_log/statistical_method_v4_contract_20261010.md"
OUT = ROOT / "research/research_corrections_20261009/cmc_calibration_v4_reference"
STAGE = "v4_reference_20261010"
CONFIRM_STAGE = "v4_confirmation_20261010"
LENGTHS = (90, 180, 365)
HISTORIES = 1000
GENERATOR_SHA = "26fb3ce192f93416f215d1c8ec2e3f7bb39489ac85c9b1f20ebc7843858369d4"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity():
    if digest(models.__file__) != GENERATOR_SHA:
        raise ValueError("historical_generator_changed")
    return {"generator_sha256": GENERATOR_SHA, "runner_sha256": digest(__file__),
            "contract_sha256": digest(PLAN), "numpy_version": models.np.__version__}


def write_new(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)


def validate_part(part, model, days, expected_identity):
    if (part.get("model") != model or part.get("days") != days
            or part.get("stage") != STAGE or part.get("identity") != expected_identity
            or type(part.get("histories")) is not int or part["histories"] != HISTORIES):
        raise ValueError("invalid_reference_identity")
    means = part.get("null_means")
    if (not isinstance(means, list) or len(means) != HISTORIES
            or any(type(x) not in (int, float) or not math.isfinite(x) for x in means)):
        raise ValueError("invalid_reference_means")
    return max(means)


def cell(model, days, expected_identity):
    means = []
    for trial in range(HISTORIES):
        history = models.generate(STAGE, model, days, 0, trial,
                                  allowed=(STAGE, CONFIRM_STAGE))
        series = models.day_series(history)
        if series is None or not models.np.isfinite(series).all():
            raise ValueError("reference_unavailable")
        means.append(float(series.mean()))
    return {"stage": STAGE, "model": model, "days": days,
            "histories": HISTORIES, "identity": expected_identity, "null_means": means}


def build(*, max_cells=18, budget_seconds=120):
    if type(max_cells) is not int or not 1 <= max_cells <= 18:
        raise ValueError("invalid_cell_budget")
    if type(budget_seconds) is not int or not 1 <= budget_seconds <= 120:
        raise ValueError("invalid_time_budget")
    ident = identity()
    expected = {f"{m}_{d}.json": (m, d) for m in models.SUPPORTED for d in LENGTHS}
    saved = {}
    for path in (OUT / "reference").glob("*.json"):
        if path.name not in expected:
            raise ValueError("unexpected_reference_file")
        m, d = expected[path.name]
        part = json.loads(path.read_text())
        validate_part(part, m, d, ident)
        saved[path.name] = part
    started, made = time.monotonic(), 0
    for name, (model, days) in expected.items():
        if name in saved:
            continue
        if made >= max_cells or time.monotonic() - started >= budget_seconds:
            return {"status": "REFERENCE_INCOMPLETE", "cells": len(saved)}
        part = cell(model, days, ident)
        validate_part(part, model, days, ident)
        write_new(OUT / "reference" / name, part)
        saved[name] = part
        made += 1
    cutoffs = {str(d): max(validate_part(saved[f"{m}_{d}.json"], m, d, ident)
                          for m in models.SUPPORTED) for d in LENGTHS}
    if any(not math.isfinite(c) or c <= 0 for c in cutoffs.values()):
        raise ValueError("invalid_reference_cutoff")
    lock = {"status": "REFERENCE_LOCKED_NOT_CERTIFIED", "identity": ident,
            "cutoffs": cutoffs, "histories_per_cell": HISTORIES,
            "reference_sha256": {name: digest(OUT / "reference" / name)
                                 for name in expected},
            "confirmation_stage": CONFIRM_STAGE, "primary_scoring_enabled": False}
    path = OUT / "lock_v4.json"
    if path.exists():
        if json.loads(path.read_text()) != lock:
            raise ValueError("existing_lock_mismatch")
    else:
        write_new(path, lock)
    return {"status": lock["status"], "cells": len(saved), "cutoffs": cutoffs,
            "confirmation_generated": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-cells", type=int, default=18)
    parser.add_argument("--budget-seconds", type=int, default=120)
    args = parser.parse_args()
    print(json.dumps(build(max_cells=args.max_cells, budget_seconds=args.budget_seconds), indent=2))
