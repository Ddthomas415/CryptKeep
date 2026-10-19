"""ENTR-CB-1 report tables (frozen prereg section 6) from saved, hash-pinned outputs only. Computes nothing new.

Reads the guarded result (checked with pinned_run_inputs.check_output against the pinned plan hash), the
declared sensitivity result, the v2 results (for the unfiltered side-by-side rows) and the listing file.
Writes (exclusive create) entrant_selections.csv (all 133 v2 entrant selections, losers included, with
filter status and both v2 and Coinbase-filtered dollars), control_removed_by_year.csv and tables.json.
"""
import argparse
import csv
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from scripts.research import pinned_run_inputs as guard


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def members_by_cycle(cycles):
    return {c["entry_date"]: {m["id"]: m for m in c["members"]} for c in cycles}


def build(result, sensitivity, v2, listings):
    assets = listings["assets"]
    cb = result["cb_cycles"]
    rows = []
    v2_entrants = v2["cycles"]["new_entrants"]
    cb_members = members_by_cycle(cb["new_entrants"])
    for cycle in v2_entrants:
        for m in cycle["members"]:
            rec = assets.get(str(m["id"]), {"status": "missing"})
            in_cb = m["id"] in cb_members.get(cycle["entry_date"], {})
            cbm = cb_members.get(cycle["entry_date"], {}).get(m["id"])
            if rec["status"] == "mapped":
                status = "tradable" if in_cb else ("not_yet_listed" if rec["first_candle"] >= cycle["entry_date"] else
                                                   "delisted_before_entry")
            else:
                status = rec["status"]
            rows.append({"selection_date": cycle["selection_date"], "entry_date": cycle["entry_date"],
                         "exit_date": cycle["exit_date"], "cmc_id": m["id"], "symbol": m["symbol"], "slug": m["slug"],
                         "cb_status": status, "cb_product": rec.get("product", ""), "cb_first_candle": rec.get("first_candle", ""),
                         "cb_last_candle": rec.get("last_candle") or "",
                         "v2_net_dollars_lower_in_v2_basket": round(m["net_dollars_lower"], 6),
                         "v2_allocation": m["allocation"],
                         "cb_net_dollars_lower": round(cbm["net_dollars_lower"], 6) if cbm else "",
                         "cb_allocation": cbm["allocation"] if cbm else ""})
    by_year = defaultdict(Counter)
    for r in rows:
        by_year[r["entry_date"][:4]][r["cb_status"]] += 1
    removed = sorted((r for r in rows if r["cb_status"] != "tradable"), key=lambda r: -r["v2_net_dollars_lower_in_v2_basket"])
    kept = sorted((r for r in rows if r["cb_status"] == "tradable"), key=lambda r: -float(r["cb_net_dollars_lower"]))
    ent_cycles = cb["new_entrants"]
    values = sorted(((c["net_dollars_lower"], c["entry_date"]) for c in ent_cycles), reverse=True)
    largest = values[0]
    ctl_removed = defaultdict(Counter)
    v2_ctl, cb_ctl = v2["cycles"]["altcoin_control"], members_by_cycle(cb["altcoin_control"])
    for cycle in v2_ctl:
        for m in cycle["members"]:
            rec = assets.get(str(m["id"]), {"status": "missing"})
            in_cb = m["id"] in cb_ctl.get(cycle["entry_date"], {})
            status = "tradable" if in_cb else (rec["status"] if rec["status"] != "mapped" else "listing_dates")
            ctl_removed[cycle["entry_date"][:4]][status] += 1
    unresolved = [{"arm": arm, "entry_date": c["entry_date"], "exit_date": c["exit_date"],
                   "ids": [m["id"] for m in c["members"] if m["status"] != "MODELLED"]}
                  for arm in ("new_entrants", "altcoin_control") for c in cb[arm] if c["unresolved_exits"] or c["missing_entries"]]
    pick = lambda s: {k: s.get(k) for k in ("cycles", "funded_cycles", "selections", "funded_selections", "distinct_ids",
                                            "mean_net_dollars_lower", "median_net_dollars_lower", "mean_gross_dollars_lower",
                                            "mean_stress_dollars_lower", "profitable_cycles_lower", "worst_cycle_dollars_lower",
                                            "unresolved_exits", "missing_entries", "point_status")}
    tables = {
        "decision": result["decision"],
        "sensitivity_xrp_gap_decision": sensitivity["decision"],
        "summary": {arm: {"coinbase_filtered": pick(result["cb_summary"][arm]),
                          "coinbase_filtered_intervals": result["cb_summary"][arm].get("mean_net_interval"),
                          "v2_unfiltered_reference": pick(result["reference_v2_summary"][arm])}
                    for arm in ("new_entrants", "altcoin_control")},
        "segments_new_entrants": {k: pick(v) for k, v in result["cb_summary"]["new_entrants"]["segments"].items()},
        "segments_control": {k: pick(v) for k, v in result["cb_summary"]["altcoin_control"]["segments"].items()},
        "paired_vs_control": result["cb_summary"]["new_entrants"]["paired_vs_control"],
        "largest_entrant_cycle": {"entry_date": largest[1], "net_dollars_lower": largest[0],
                                  "members": [m for c in ent_cycles if c["entry_date"] == largest[1] for m in c["members"]]},
        "filter_accounting": result["filter_accounting"],
        "entrant_selections_by_year": {y: dict(c) for y, c in sorted(by_year.items())},
        "control_selections_by_year": {y: dict(c) for y, c in sorted(ctl_removed.items())},
        "top_kept_entrant_selections": kept[:10],
        "top_removed_entrant_selections_by_v2_dollars": removed[:10],
        "unresolved_or_missing": unresolved,
        "unknown_listing_ids": sorted(int(k) for k, v in assets.items() if v["status"] == "unknown"),
    }
    return rows, tables


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("--result-dir", "--sensitivity-dir", "--v2-results", "--listings", "--output-dir"):
        parser.add_argument(name, type=Path, required=True)
    for name in ("--plan-sha256", "--sensitivity-plan-sha256", "--v2-results-sha256", "--listings-sha256"):
        parser.add_argument(name, required=True)
    args = parser.parse_args(argv)
    result = guard.check_output(args.result_dir, expected_plan_sha256=args.plan_sha256)
    sensitivity = guard.check_output(args.sensitivity_dir, expected_plan_sha256=args.sensitivity_plan_sha256)
    for path, expected in ((args.v2_results, args.v2_results_sha256), (args.listings, args.listings_sha256)):
        if sha(path) != expected:
            raise SystemExit(f"pinned input changed or unexpected: {path}")
    if result["provenance"]["listings_sha256"] != args.listings_sha256:
        raise SystemExit("listing file is not the one the result was computed from")
    rows, tables = build(result, sensitivity, json.loads(args.v2_results.read_bytes()), json.loads(args.listings.read_bytes()))
    tables["inputs"] = {"result_sha256": sha(args.result_dir / "result.json"), "plan_sha256": args.plan_sha256,
                        "sensitivity_result_sha256": sha(args.sensitivity_dir / "result.json"),
                        "sensitivity_plan_sha256": args.sensitivity_plan_sha256,
                        "v2_results_sha256": args.v2_results_sha256, "listings_sha256": args.listings_sha256}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with open(args.output_dir / "entrant_selections.csv", "x", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(args.output_dir / "control_removed_by_year.csv", "x", newline="") as stream:
        statuses = sorted({s for c in tables["control_selections_by_year"].values() for s in c})
        w = csv.writer(stream)
        w.writerow(["entry_year"] + statuses)
        for year, c in tables["control_selections_by_year"].items():
            w.writerow([year] + [c.get(s, 0) for s in statuses])
    with open(args.output_dir / "tables.json", "x") as stream:
        json.dump(tables, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"entrant_rows": len(rows), "by_year": tables["entrant_selections_by_year"],
                      "decision": tables["decision"]["verdict"], "sensitivity": tables["sensitivity_xrp_gap_decision"]["verdict"]}))


if __name__ == "__main__":
    main()
