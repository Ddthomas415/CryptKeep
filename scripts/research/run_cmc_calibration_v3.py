"""Run v3 size-only calibration: develop -> lock -> (after independent review) confirm -> summarize.

All outputs are written with open("x") (never overwritten). Synthetic data only; no market data read.
"""
import argparse
import collections
import hashlib
import json
import math
import time
from pathlib import Path

from scripts.research import cmc_calibration_v3 as v3

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research/research_corrections_20261009/cmc_calibration_v3"
DEV_CELLS = [(m, d) for m in v3.SUPPORTED for d in (90, 365)]
DEV_HISTORIES, CONF_HISTORIES, TOLERANCE = 10, 1000, .075
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
PLAN = ROOT / "docs/research/cmc_trending_log/statistical_method_v3_PLAN_20261009.md"
EXPECTED_CELLS = {(m, d, i) for m in v3.MODELS for d in (90, 180, 365) for i in range(4)}


def experiment_identity():
    return {"module_sha256": sha(v3.__file__), "runner_sha256": sha(__file__),
            "plan_sha256": sha(PLAN), "numpy_version": v3.np.__version__}


def validated_lock():
    lock = json.loads((OUT / "lock_v3.json").read_text())
    if (lock.get("identity") != experiment_identity()
            or lock.get("locked_method") not in v3.METHODS
            or lock.get("locked_before_confirmation") is not True):
        raise ValueError("invalid_or_changed_experiment_lock")
    return lock


def validate_acceptance(lock_hash):
    acceptance = json.loads((OUT / "review_accepted_v3.json").read_text())
    if (acceptance.get("lock_sha256") != lock_hash
            or acceptance.get("identity") != experiment_identity()
            or acceptance.get("status") not in ("ACCEPTED", "ACCEPTED_WITH_RISK")):
        raise ValueError("missing_matching_independent_acceptance")


def validate_part(part, lock_hash, expected_cell=None):
    model, days, mi = (part.get(k) for k in ("model", "days", "mean_index"))
    if (not isinstance(model, str) or type(days) is not int or type(mi) is not int
            or (model, days, mi) not in EXPECTED_CELLS
            or (expected_cell is not None and (model, days, mi) != expected_cell)):
        raise ValueError("invalid_confirmation_cell")
    mean = part.get("mean")
    if (type(mean) not in (int, float) or not math.isfinite(mean) or mean != v3.MEANS[mi]
            or part.get("lock_sha256") != lock_hash
            or type(part.get("histories")) is not int or part["histories"] != CONF_HISTORIES):
        raise ValueError("confirmation_identity_or_history_mismatch")
    counts = part.get("status_counts")
    if (not isinstance(counts, dict) or not counts
            or not set(counts) <= {"AVAILABLE", "UNAVAILABLE", "REFUSED"}
            or any(type(n) is not int or n < 0 for n in counts.values())
            or sum(counts.values()) != CONF_HISTORIES):
        raise ValueError("invalid_confirmation_status_counts")
    positives = part.get("positives")
    if type(positives) is not int or not 0 <= positives <= counts.get("AVAILABLE", 0):
        raise ValueError("invalid_confirmation_positive_count")
    return model, days, mi


def write_new(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as fh:
        json.dump(payload, fh, indent=1, allow_nan=False)


def develop():
    results = {}
    for method in v3.METHODS:
        worst, available_everywhere, cells = -1, True, {}
        for model, days in DEV_CELLS:
            rows = [v3.evaluate(method, "v3_development", model, days, 0, t) for t in range(DEV_HISTORIES)]
            fp = sum(r.get("positive") is True for r in rows)
            avail = sum(r["status"] == "AVAILABLE" for r in rows)
            cells[f"{model}|{days}"] = {"false_positives": fp, "available": avail}
            worst = max(worst, fp)
            available_everywhere &= avail > 0
        results[method] = {"worst_cell_false_positives": worst, "available_in_every_cell": available_everywhere,
                           "cells": cells}
    survivors = [m for m in v3.METHODS if results[m]["available_in_every_cell"]]
    locked = min(survivors, key=lambda m: (results[m]["worst_cell_false_positives"], v3.METHODS.index(m))) \
        if survivors else None
    payload = {"stage": "v3_development", "histories_per_cell": DEV_HISTORIES, "cells": DEV_CELLS,
               "results": results, "locked_method": locked or "NO_METHOD_LOCKED",
               "selection_rule": "lowest worst-cell false positives; ties C, B, A; unavailable methods filtered first",
               "module_sha256": sha(v3.__file__), "runner_sha256": sha(__file__)}
    write_new(OUT / "development_v3.json", payload)
    if locked:
        write_new(OUT / "lock_v3.json", {"locked_method": locked, "identity": experiment_identity(),
                                         "locked_before_confirmation": True})
    return payload


def confirm(cells_per_call):
    if type(cells_per_call) is not int or cells_per_call <= 0:
        raise ValueError("positive_cell_budget_required")
    lock = validated_lock()
    lock_hash = sha(OUT / "lock_v3.json")
    validate_acceptance(lock_hash)
    seen = set()
    for path in (OUT / "confirmation").glob("*.json"):
        cell = validate_part(json.loads(path.read_text()), lock_hash)
        if cell in seen or path.name != f"{cell[0]}_{cell[1]}_{cell[2]}.json":
            raise ValueError("duplicate_or_misnamed_confirmation_cell")
        seen.add(cell)
    done = 0
    for model in v3.MODELS:
        for days in (90, 180, 365):
            for mi in range(4):
                part = OUT / "confirmation" / f"{model}_{days}_{mi}.json"
                if part.exists():
                    validate_part(json.loads(part.read_text()), lock_hash, (model, days, mi))
                    continue
                if done >= cells_per_call:
                    return done
                t0 = time.time()
                rows = [v3.evaluate(lock["locked_method"], "v3_confirmation", model, days, mi, t)
                        for t in range(CONF_HISTORIES)]
                write_new(part, {"model": model, "days": days, "mean_index": mi, "mean": v3.MEANS[mi],
                                 "status_counts": dict(collections.Counter(r["status"] for r in rows)),
                                 "positives": sum(r.get("positive") is True for r in rows),
                                 "histories": CONF_HISTORIES, "seconds": round(time.time()-t0, 2),
                                 "lock_sha256": sha(OUT / "lock_v3.json")})
                done += 1
    return done


def summarize():
    lock = validated_lock()
    lock_hash = sha(OUT / "lock_v3.json")
    validate_acceptance(lock_hash)
    parts = [json.loads(p.read_text()) for p in sorted((OUT / "confirmation").glob("*.json"))]
    cells = [validate_part(p, lock_hash) for p in parts]
    if len(cells) != len(set(cells)) or set(cells) != EXPECTED_CELLS:
        raise ValueError("incomplete_or_duplicate_confirmation_grid")
    size, power, refusal = [], [], []
    for p in parts:
        avail = p["status_counts"].get("AVAILABLE", 0)
        lo, hi = v3.wilson(p["positives"], p["histories"])
        row = {"model": p["model"], "days": p["days"], "mean": p["mean"], "positives": p["positives"],
               "available": avail, "wilson95": [lo, hi]}
        if p["model"] not in v3.SUPPORTED:
            row["refused_all"] = p["status_counts"].get("REFUSED", 0) == p["histories"]
            refusal.append(row)
        elif p["mean"] == 0:
            row["passes"] = avail == p["histories"] and hi <= TOLERANCE
            size.append(row)
        else:
            power.append(row)
    certified = all(r["passes"] for r in size) and all(r["refused_all"] for r in refusal)
    payload = {"result": "SIZE_TOLERANCE_MET_POINTWISE" if certified else "NO_CERTIFIED_SAMPLE_V3",
               "locked_method": lock["locked_method"], "tolerance_wilson_upper": TOLERANCE,
               "size_cells": size, "power_cells_descriptive": power, "refusal_cells": refusal,
               "meaning": "pointwise synthetic size control only; power reported, not required (operator 2026-10-09)",
               "lock_sha256": sha(OUT / "lock_v3.json")}
    write_new(OUT / "confirmation_summary_v3.json", payload)
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["develop", "confirm", "summarize"])
    ap.add_argument("--cells", type=int, default=12)
    a = ap.parse_args()
    if a.mode == "develop":
        r = develop(); print(r["locked_method"], {m: v["worst_cell_false_positives"] for m, v in r["results"].items()})
    elif a.mode == "confirm":
        print("cells written", confirm(a.cells))
    else:
        r = summarize(); print(r["result"])
