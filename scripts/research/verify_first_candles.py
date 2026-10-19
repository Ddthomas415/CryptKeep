"""ENTR-CB-1 Step B check: confirm each first daily candle that decides a selection, by scanning earlier windows.

fetch_coinbase_listing_dates.py finds first candles by binary search (frozen prereg section 4). Its
documented limit is a trading gap covering a whole 300-day window: the search can then return a later
first date. SHOWN on the saved data: XRP-USD came back as first 2023-07-13 although XRP traded on
Coinbase before its 2021 suspension. This script repairs that without changing the rule: for every
mapped asset whose found first candle is after its earliest selection date (so the first candle
decides at least one selection), it fetches, in date order, each window before the found first window
that the search did not query, for each of the asset's products, stopping at the first window with
candles. Same endpoint, request form, rate limit and logging as the fetcher (its Fetcher class);
separate output directory; hard cap.

Output results_verified.json: the fetcher's results.json with "first" replaced by the earliest candle
found here where earlier, and per product a "first_check" record (windows checked, candle counts,
found vs verified first). Empty windows between a verified first and the found first are trading gaps;
they are reported, and the frozen first/last rule still treats the asset as listed across them.
"""
import argparse
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
import time

from scripts.research import fetch_coinbase_listing_dates as fetch


def targets(identity_map, results, control_rows):
    """{product: [window indices to check]} for assets whose found first candle follows their first selection."""
    wins = fetch.windows(date.fromisoformat(results["end_day"]))
    first_entry = {r["cmc_id"]: date.fromisoformat(r["first_entry"]) for r in control_rows}
    out = {}
    for cmc_id, rec in identity_map["records"].items():
        if rec["status"] != "mapped":
            continue
        names = [p["id"] for p in rec["products"]]
        firsts = [date.fromisoformat(results["products"][p]["first"]) for p in names if results["products"][p]["first"]]
        if not firsts or min(firsts) < first_entry[cmc_id]:
            continue  # listed before every selection: an earlier first changes nothing
        for p in names:
            v = results["products"][p]
            if v["first"] is None:
                continue
            k = max(i for i, w in enumerate(wins) if w[0] <= date.fromisoformat(v["first"]))
            queried = {w for w, _ in v["windows_queried"]}
            todo = [i for i in range(k) if wins[i][0].isoformat() not in queried]
            if todo:
                out[p] = sorted(set(out.get(p, [])) | set(todo))
    return out, wins


def verify(todo, wins, results, out, max_requests, budget, get=fetch.http_get, sleep=time.sleep, clock=time.monotonic):
    began = clock()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    state_path = out / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"done": {}}
    state["requests"] = fetch.logged_request_count(out)
    fetcher = fetch.Fetcher(out, state, max_requests, get=get, sleep=sleep, clock=clock)
    stopped = None
    try:
        for product in sorted(todo):
            if product in state["done"]:
                continue
            if clock() - began > budget:
                stopped = "budget"
                break
            trail, earliest, error = [], None, None
            try:
                for i in todo[product]:
                    days = fetcher.window_days(product, wins[i], trail)
                    if days:
                        earliest = days[0]
                        break
            except fetch.ProductFailed as failure:
                error = str(failure)
            state["done"][product] = {"windows_checked": trail, "earliest_found": earliest and earliest.isoformat(),
                                      "error": error}
            fetch.write_json_atomic(state_path, state)
    except fetch.RequestCapReached:
        stopped = "request_cap"
    finally:
        fetch.write_json_atomic(state_path, state)
    return state, stopped


def merged(results, state, todo):
    doc = json.loads(json.dumps(results))
    for product, check in state["done"].items():
        v = doc["products"][product]
        found = v["first"]
        verified = check["earliest_found"] if check["earliest_found"] and check["earliest_found"] < found else found
        # windows the binary search found empty, lying between the verified and the found first candle
        gaps = [w for w, n in v["windows_queried"] if n == 0 and verified < w < found]
        v["first_check"] = {"found_first": found, "verified_first": verified, "windows_checked": check["windows_checked"],
                            "windows_planned": len(todo[product]), "error": check["error"], "empty_windows_after_verified_first": gaps}
        if check["error"]:
            v["error"] = "first_check_" + check["error"]
        v["first"] = verified
        v["first_at_search_start"] = verified == doc["search_start"]
    doc["first_check"] = {"products_checked": len(state["done"]), "requests": state["requests"]}
    return doc


def main(argv=None, get=fetch.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("--map", "--results", "--control-ids", "--output-dir"):
        parser.add_argument(name, type=Path, required=True)
    for name in ("--map-sha256", "--results-sha256", "--control-ids-sha256"):
        parser.add_argument(name, required=True)
    parser.add_argument("--max-requests", type=int, default=400)
    parser.add_argument("--budget-seconds", type=float, default=120)
    args = parser.parse_args(argv)
    for path, expected in ((args.map, args.map_sha256), (args.results, args.results_sha256),
                           (args.control_ids, args.control_ids_sha256)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"pinned input changed or unexpected: {path}")
    identity_map = json.loads(args.map.read_bytes())
    results = json.loads(args.results.read_bytes())
    if results["map_sha256"] != args.map_sha256:
        raise SystemExit("results were not fetched for this map")
    todo, wins = targets(identity_map, results, list(csv.DictReader(open(args.control_ids))))
    state, stopped = verify(todo, wins, results, args.output_dir, args.max_requests, args.budget_seconds, get, sleep)
    remaining = [p for p in todo if p not in state["done"]]
    if not remaining and not (args.output_dir / "results_verified.json").exists():
        doc = merged(results, state, todo)
        doc["first_check"]["source_results_sha256"] = args.results_sha256
        with open(args.output_dir / "results_verified.json", "x") as stream:
            json.dump(doc, stream, indent=2, sort_keys=True)
    changed = sorted(p for p, c in state["done"].items()
                     if c["earliest_found"] and c["earliest_found"] < results["products"][p]["first"])
    summary = {"products_planned": len(todo), "windows_planned": sum(map(len, todo.values())),
               "products_done": len(state["done"]), "requests_total": state["requests"], "stopped": stopped,
               "first_moved_earlier": changed, "errors": sorted(p for p, c in state["done"].items() if c["error"])}
    print(json.dumps(summary))
    return summary


if __name__ == "__main__":
    main()
