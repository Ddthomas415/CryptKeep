"""Fresh finite-family confirmation only; never enables market scoring."""
import argparse
import collections
import json
import math
import time

from scripts.research import run_cmc_reference_v4 as ref

MODELS = ref.models
EXPECTED = {(m, d, i) for m in MODELS.MODELS for d in ref.LENGTHS for i in range(4)}


def context():
    lock_path = ref.OUT / "lock_v4.json"
    lock = json.loads(lock_path.read_text())
    if lock.get("identity") != ref.identity() or lock.get("primary_scoring_enabled") is not False:
        raise ValueError("invalid_reference_lock")
    # Reconstruct the entire reviewed reference rather than trusting cutoffs alone.
    expected_files = {f"{m}_{d}.json" for m in MODELS.SUPPORTED for d in ref.LENGTHS}
    paths = {p.name: p for p in (ref.OUT / "reference").glob("*.json")}
    if set(paths) != expected_files or set(lock.get("reference_sha256", {})) != expected_files:
        raise ValueError("reference_grid_mismatch")
    maxima = {}
    for m in MODELS.SUPPORTED:
        for d in ref.LENGTHS:
            name = f"{m}_{d}.json"
            if ref.digest(paths[name]) != lock["reference_sha256"][name]:
                raise ValueError("reference_hash_mismatch")
            value = ref.validate_part(json.loads(paths[name].read_text()), m, d, ref.identity())
            maxima[str(d)] = max(maxima.get(str(d), -math.inf), value)
    if maxima != lock.get("cutoffs") or any(c <= 0 for c in maxima.values()):
        raise ValueError("cutoff_mismatch")
    ident = {"lock_sha256": ref.digest(lock_path), "confirmation_runner_sha256": ref.digest(__file__)}
    accepted = json.loads((ref.OUT / "confirmation_review_accepted.json").read_text())
    if (accepted.get("identity") != ident
            or accepted.get("status") not in ("ACCEPTED", "ACCEPTED_WITH_RISK")):
        raise ValueError("independent_review_required")
    return lock, ident


def validate(part, ident):
    m, d, i = (part.get(k) for k in ("model", "days", "mean_index"))
    if (type(m) is not str or type(d) is not int or type(i) is not int
            or (m, d, i) not in EXPECTED or part.get("identity") != ident
            or part.get("stage") != ref.CONFIRM_STAGE
            or type(part.get("histories")) is not int or part["histories"] != 1000
            or type(part.get("mean")) not in (int, float) or part["mean"] != MODELS.MEANS[i]):
        raise ValueError("confirmation_contract_mismatch")
    counts = part.get("status_counts")
    if (not isinstance(counts, dict) or not counts
            or not set(counts) <= {"AVAILABLE", "REFUSED"}
            or any(type(n) is not int or n < 0 for n in counts.values())
            or sum(counts.values()) != 1000
            or type(part.get("positives")) is not int
            or not 0 <= part["positives"] <= counts.get("AVAILABLE", 0)):
        raise ValueError("invalid_confirmation_counts")
    return m, d, i


def parts(ident):
    saved = {}
    for path in (ref.OUT / "confirmation").glob("*.json"):
        part = json.loads(path.read_text())
        cell = validate(part, ident)
        if cell in saved or path.name != f"{cell[0]}_{cell[1]}_{cell[2]}.json":
            raise ValueError("duplicate_or_misnamed_cell")
        saved[cell] = part
    return saved


def confirm(*, budget_seconds=120):
    if type(budget_seconds) is not int or not 1 <= budget_seconds <= 120:
        raise ValueError("invalid_time_budget")
    lock, ident = context()
    saved = parts(ident)
    started = time.monotonic()
    for m, d, i in sorted(EXPECTED):
        if (m, d, i) in saved:
            continue
        if time.monotonic() - started >= budget_seconds:
            return {"status": "CONFIRMATION_INCOMPLETE", "cells": len(saved)}
        statuses, positives = collections.Counter(), 0
        for trial in range(1000):
            history = MODELS.generate(ref.CONFIRM_STAGE, m, d, i, trial,
                                      allowed=(ref.STAGE, ref.CONFIRM_STAGE))
            series = MODELS.day_series(history)
            if series is None:
                statuses["REFUSED"] += 1
            elif not MODELS.np.isfinite(series).all():
                raise ValueError("nonfinite_confirmation_series")
            else:
                statuses["AVAILABLE"] += 1
                positives += int(float(series.mean()) > lock["cutoffs"][str(d)])
        part = {"model": m, "days": d, "mean_index": i, "mean": MODELS.MEANS[i],
                "stage": ref.CONFIRM_STAGE, "histories": 1000, "identity": ident,
                "status_counts": dict(statuses), "positives": positives}
        validate(part, ident)
        ref.write_new(ref.OUT / "confirmation" / f"{m}_{d}_{i}.json", part)
        saved[m, d, i] = part
    return {"status": "CONFIRMATION_COMPLETE", "cells": len(saved)}


def summarize():
    _, ident = context()
    saved = parts(ident)
    if set(saved) != EXPECTED:
        raise ValueError("incomplete_confirmation_grid")
    nulls, power, refusals = [], [], []
    for (m, d, i), part in sorted(saved.items()):
        upper = MODELS.wilson(part["positives"], 1000)[1]
        row = {"model": m, "days": d, "mean": MODELS.MEANS[i],
               "positives": part["positives"], "wilson95_upper": upper}
        if m not in MODELS.SUPPORTED:
            row["passes"] = part["status_counts"].get("REFUSED", 0) == 1000
            refusals.append(row)
        elif i == 0:
            row["passes"] = part["status_counts"].get("AVAILABLE", 0) == 1000 and upper <= .075
            nulls.append(row)
        else:
            power.append(row)
    passed = all(r["passes"] for r in nulls + refusals)
    result = {"status": "FINITE_FAMILY_REFERENCE_ONLY" if passed else "NO_CERTIFIED_REFERENCE_V4",
              "identity": ident, "null_cells": nulls, "descriptive_power": power,
              "refusal_cells": refusals, "primary_scoring_enabled": False,
              "not_market_inference": True}
    path = ref.OUT / "confirmation_summary_v4.json"
    if path.exists():
        if json.loads(path.read_text()) != result:
            raise ValueError("existing_summary_mismatch")
    else:
        ref.write_new(path, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("confirm", "summarize"))
    args = parser.parse_args()
    result = confirm() if args.mode == "confirm" else summarize()
    print(json.dumps(result, indent=2))
