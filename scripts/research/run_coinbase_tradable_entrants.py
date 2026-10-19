"""ENTR-CB-1 runner: frozen v2 entrant rule restricted to Coinbase-tradable coins.

Implements docs/research/coinbase_tradable_entrants_20261019/PREREGISTRATION_DRAFT.md.
Reuses the unchanged v2 cohort engine (choose, cycle, describe, interval) and
the v2 identity correction; adds only a per-cycle Coinbase-tradability filter
applied to each cycle's selected members before equal weights are set.

main() refuses to run until FROZEN_PREREG_SHA256 is set to the operator-frozen
preregistration hash (a reviewed code change at freeze time). The pure
functions below are exercised on synthetic data by tests; no market data is
read on import. Prices remain CMC reference prices, not Coinbase fills.

Listing file (JSON), produced only after the approved Coinbase probe:

    {"schema": "entr-cb1-listings-v1",
     "assets": {"<cmc_id>": {"status": "mapped", "product": "XYZ-USD",
                             "first_candle": "2021-03-04", "last_candle": null}}}

status is one of: "mapped" (first_candle required; last_candle null while still
trading), "never_listed" (verified absent from Coinbase), "unknown" (identity or
listing history could not be established). Every selected CMC ID must appear;
a missing ID refuses the run.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import statistics

from scripts.research import run_low_value_top100_v2 as v2
from scripts.research import test_low_value_top100 as engine

FROZEN_PREREG_SHA256 = "a7fb3662450b20764f1d11404543b9551283a3c50f290ab466d3b02db86c67e9"  # frozen 2026-10-19T05:46:38Z
V2_RUNNER_SHA256 = "04ab5aa238ca523c3965e9a984d2be3a315c92f3cc64327d5b9016a1a786b50d"
LISTING_SCHEMA = "entr-cb1-listings-v1"
ARMS = ("new_entrants", "altcoin_control")
STATUSES = {"mapped", "never_listed", "unknown"}
MIN_FUNDED_CYCLES = 30
MAX_SHARE = 0.10


def _day(value, label):
    if type(value) is not str:
        raise ValueError(f"bad date for {label}")
    return date.fromisoformat(value)


def _refuse_constant(name):
    raise ValueError(f"non-finite JSON constant {name}")


def parse_listings(raw):
    """Validate a listing document; return {cmc_id: record}. Refuses anything malformed."""
    doc = json.loads(raw, parse_constant=_refuse_constant)
    if type(doc) is not dict or doc.get("schema") != LISTING_SCHEMA or type(doc.get("assets")) is not dict:
        raise ValueError("bad listing document")
    assets = {}
    for key, rec in doc["assets"].items():
        if not key.isdigit() or int(key) <= 0 or str(int(key)) != key:
            raise ValueError(f"bad CMC id {key!r}")
        if type(rec) is not dict or rec.get("status") not in STATUSES:
            raise ValueError(f"bad listing status for {key}")
        if rec["status"] == "mapped":
            if set(rec) != {"status", "product", "first_candle", "last_candle"}:
                raise ValueError(f"bad mapped record for {key}")
            if type(rec["product"]) is not str or "-" not in rec["product"]:
                raise ValueError(f"bad product for {key}")
            first = _day(rec["first_candle"], key)
            last = None if rec["last_candle"] is None else _day(rec["last_candle"], key)
            if last is not None and last < first:
                raise ValueError(f"last candle before first for {key}")
            assets[int(key)] = {"status": "mapped", "product": rec["product"], "first": first, "last": last}
        else:
            if set(rec) != {"status"}:
                raise ValueError(f"bad {rec['status']} record for {key}")
            assets[int(key)] = {"status": rec["status"]}
    return assets


def classify(listings, identity, entry_day):
    """Return 'tradable', 'not_yet_listed', 'delisted_before_entry', 'never_listed' or 'unknown'."""
    if identity not in listings:
        raise ValueError(f"listing file lacks selected CMC id {identity}")
    rec = listings[identity]
    if rec["status"] != "mapped":
        return rec["status"]
    if rec["first"] > entry_day - timedelta(days=1):
        return "not_yet_listed"
    if rec["last"] is not None and rec["last"] < entry_day:
        return "delisted_before_entry"
    return "tradable"


def delisted_before(listings, identity, exit_day):
    rec = listings[identity]
    return rec["status"] == "mapped" and rec["last"] is not None and rec["last"] < exit_day


def _summaries(cycles):
    summary = {}
    for arm in ARMS:
        full = engine.describe(cycles[arm])
        full["segments"] = {
            label: engine.describe([c for c in cycles[arm] if (c["entry_date"] < "2023") == early])
            for label, early in (("2019_2022", True), ("2023_onward", False))
        }
        summary[arm] = full
    paired = [a["net_dollars_lower"] - b["net_dollars_lower"]
              if a["unresolved_exits"] == b["unresolved_exits"] == 0 else None
              for a, b in zip(cycles["new_entrants"], cycles["altcoin_control"])]
    summary["new_entrants"]["paired_vs_control"] = engine.interval(paired)
    summary["new_entrants"]["paired_vs_control"]["excluded_cycles"] = sum(v is None for v in paired)
    return summary, paired


def run_filtered(dates, snapshots, listings):
    """Unfiltered (v2 reference) and Coinbase-filtered cycles for both arms."""
    first = next(i for i, d in enumerate(dates) if d >= date(2019, 1, 1))
    reference = {arm: [] for arm in ARMS}
    filtered = {arm: [] for arm in ARMS}
    accounting = {arm: {"selections_before_filter": 0, "tradable": 0, "not_yet_listed": 0,
                        "delisted_before_entry": 0, "never_listed": 0, "unknown": 0,
                        "exits_unresolved_by_delisting": 0, "removed_ids": {}} for arm in ARMS}
    for index in range(max(4, first), len(dates) - 5, 4):
        choices = engine.choose(snapshots, index)
        entry_day, exit_day = dates[index + 1], dates[index + 5]
        stamp = dict(selection_date=dates[index].isoformat(), entry_date=entry_day.isoformat(),
                     exit_date=exit_day.isoformat())
        for arm in ARMS:
            ref = engine.cycle(choices[arm], snapshots[index], snapshots[index + 1], snapshots[index + 5])
            ref.update(stamp)
            reference[arm].append(ref)
            acc = accounting[arm]
            kept = []
            for identity in choices[arm]:
                acc["selections_before_filter"] += 1
                state = classify(listings, identity, entry_day)
                acc[state] += 1
                if state == "tradable":
                    kept.append(identity)
                else:
                    acc["removed_ids"].setdefault(state, []).append(identity)
            exit_view = dict(snapshots[index + 5])
            for identity in kept:
                if delisted_before(listings, identity, exit_day) and identity in exit_view:
                    del exit_view[identity]
                    acc["exits_unresolved_by_delisting"] += 1
            res = engine.cycle(kept, snapshots[index], snapshots[index + 1], exit_view)
            res.update(stamp)
            filtered[arm].append(res)
    for arm in ARMS:
        accounting[arm]["removed_ids"] = {k: sorted(set(v)) for k, v in accounting[arm]["removed_ids"].items()}
    ref_summary, _ = _summaries(reference)
    cb_summary, paired = _summaries(filtered)
    decision = decide(filtered["new_entrants"], paired, cb_summary["new_entrants"],
                      accounting["new_entrants"])
    return {"cb_summary": cb_summary, "reference_v2_summary": ref_summary,
            "cb_cycles": filtered, "filter_accounting": accounting, "decision": decision}


def decide(entrant_cycles, paired, entrant_summary, entrant_accounting):
    """Apply the preregistered CONTINUE / STOP / INCONCLUSIVE rule (section 5)."""
    values = [c["net_dollars_lower"] for c in entrant_cycles]
    mean = statistics.mean(values) if values else 0.0
    if len(values) > 1:
        rest = sorted(values)[:-1]  # drop the single largest cycle
        mean_without_largest = statistics.mean(rest)
    else:
        mean_without_largest = 0.0
    observed = [v for v in paired if v is not None]
    paired_mean = statistics.mean(observed) if observed else None
    funded = entrant_summary.get("funded_cycles", 0)
    before = entrant_accounting["selections_before_filter"]
    unknown_share = entrant_accounting["unknown"] / before if before else 1.0
    funded_selections = entrant_summary.get("funded_selections", 0)
    unresolved_share = (entrant_summary.get("unresolved_exits", 0) / funded_selections
                        if funded_selections else 1.0)
    c1 = mean > 0
    c2 = mean_without_largest > 0
    c3 = paired_mean is not None and paired_mean > 0
    c4 = funded >= MIN_FUNDED_CYCLES and unknown_share <= MAX_SHARE and unresolved_share <= MAX_SHARE
    if not (c1 and c3):
        verdict = "STOP"
    elif not (c2 and c4):
        verdict = "INCONCLUSIVE"
    else:
        verdict = "CONTINUE"
    return {"verdict": verdict,
            "c1_mean_net_lower_gt_0": {"value": mean, "pass": c1},
            "c2_mean_without_largest_cycle_gt_0": {"value": mean_without_largest, "pass": c2},
            "c3_paired_mean_vs_cb_control_gt_0": {"value": paired_mean, "paired_cycles": len(observed), "pass": c3},
            "c4_sample_and_unknowns": {"funded_cycles": funded, "min_funded_cycles": MIN_FUNDED_CYCLES,
                                       "unknown_share_of_v2_entrant_selections": unknown_share,
                                       "unresolved_share_of_cb_funded_selections": unresolved_share,
                                       "max_share": MAX_SHARE, "pass": c4},
            "note": "Exploratory direction only; intervals are reported but are not part of the rule."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("--archive", "--input-manifest", "--listings", "--prereg", "--output"):
        parser.add_argument(name, type=Path, required=True)
    parser.add_argument("--listings-sha256", required=True)
    args = parser.parse_args()
    if FROZEN_PREREG_SHA256 is None:
        raise SystemExit("preregistration not frozen: refusing to compute")
    checks = ((args.prereg, FROZEN_PREREG_SHA256), (Path(v2.__file__), V2_RUNNER_SHA256),
              (Path(engine.__file__), v2.ENGINE_HASH), (v2.ARTIFACTS / "PROTOCOL.md", engine.PROTOCOL_HASH),
              (v2.ARTIFACTS / "instrument_correction_v2.json", v2.MAP_HASH),
              (v2.ARTIFACTS / "CORRECTION_V2.md", v2.DELTA_HASH), (args.listings, args.listings_sha256))
    for path, expected in checks:
        if engine.digest(path) != expected:
            raise SystemExit(f"pinned input changed or unexpected: {path}")
    listings = parse_listings(args.listings.read_bytes())
    mapping = json.loads((v2.ARTIFACTS / "instrument_correction_v2.json").read_text())
    dates, snapshots, hashes = engine.load(args.archive, args.input_manifest)
    result = run_filtered(dates, v2.corrected_view(snapshots, mapping), listings)
    result["provenance"] = {
        "evidence": "MODELLED_EXPLORATORY_CMC_REFERENCE_PRICES_COINBASE_LISTING_FILTER",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": engine.digest(__file__), "prereg_sha256": FROZEN_PREREG_SHA256,
        "v2_runner_sha256": V2_RUNNER_SHA256, "engine_sha256": v2.ENGINE_HASH,
        "listings_sha256": args.listings_sha256, "archive_sha256": engine.digest(args.archive),
        "manifest_sha256": engine.digest(args.input_manifest), "weekly_member_sha256": hashes,
    }
    with args.output.open("x") as target:
        json.dump(result, target, indent=2, allow_nan=False)
        target.write("\n")
    print(json.dumps(result["decision"], indent=2))


if __name__ == "__main__":
    main()
