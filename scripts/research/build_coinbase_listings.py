"""ENTR-CB-1 Step B: build the runner's listing file from the frozen identity map and fetched candle dates.

Inputs, both hash-pinned by the caller: the frozen identity map (identity_map_v2/identity_map.json)
and results.json from fetch_coinbase_listing_dates.py, which must have been fetched for that same map.
Outputs (exclusive create): listings.json in the runner's schema "entr-cb1-listings-v1", and
listings_report.json with every per-asset detail behind it.

Per CMC ID in the map:
- map "never_listed" -> never_listed; map "unknown" -> unknown.
- map "mapped":
  - any of its products failed to fetch -> unknown (reason recorded);
  - none of its products has any daily candle -> unknown (listing history not established);
  - otherwise first_candle = earliest first candle over its USD/USDC/USDT products and product =
    the product holding it (ties: alphabetical); last_candle = latest last candle over its products,
    or null when that is within STILL_TRADING_DAYS of the fetch's end day ("still trading").
Asset-level union of products: the frozen rule is worded per product. The union differs from it
only when one product's trading ends before another's begins; every such gap between product
intervals is listed in the report (product_interval_gaps), together with first_at_search_start
(first candle on 2018-12-15 means on or before that day) and the windows each search queried.
"""
import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

LISTING_SCHEMA = "entr-cb1-listings-v1"
RESULTS_SCHEMA = "entr-cb1-stepB-candle-dates-v1"
STILL_TRADING_DAYS = 7


def build(identity_map, results, map_sha256):
    if results.get("schema") != RESULTS_SCHEMA or results.get("map_sha256") != map_sha256:
        raise ValueError("candle results were not fetched for this identity map")
    end_day = date.fromisoformat(results["end_day"])
    fetched = results["products"]
    assets, report = {}, {}
    for cmc_id, rec in sorted(identity_map["records"].items(), key=lambda kv: int(kv[0])):
        if rec["status"] in ("never_listed", "unknown"):
            assets[cmc_id] = {"status": rec["status"]}
            report[cmc_id] = {"status": rec["status"], "reason": "identity_map: " + rec["reason"]}
            continue
        if rec["status"] != "mapped":
            raise ValueError(f"unexpected map status for {cmc_id}")
        names = sorted(p["id"] for p in rec["products"])
        missing = [p for p in names if p not in fetched]
        if missing:
            raise ValueError(f"no candle result for {missing} (CMC id {cmc_id})")
        detail = {p: fetched[p] for p in names}
        failed = [p for p in names if fetched[p]["error"]]
        if failed:
            assets[cmc_id] = {"status": "unknown"}
            report[cmc_id] = {"status": "unknown", "reason": "candle_fetch_failed: " + ", ".join(
                f"{p} {fetched[p]['error']}" for p in failed), "products": detail}
            continue
        traded = [p for p in names if fetched[p]["first"] is not None]
        if not traded:
            assets[cmc_id] = {"status": "unknown"}
            report[cmc_id] = {"status": "unknown", "reason": "no_candles_on_any_product", "products": detail}
            continue
        spans = sorted((date.fromisoformat(fetched[p]["first"]), date.fromisoformat(fetched[p]["last"]), p)
                       for p in traded)
        first, _, product = spans[0]
        last = max(s[1] for s in spans)
        gaps, reach = [], spans[0][1]
        for start, stop, name in spans[1:]:
            if start > reach + timedelta(days=1):
                gaps.append({"from": (reach + timedelta(days=1)).isoformat(),
                             "to": (start - timedelta(days=1)).isoformat(), "resumed_on": name})
            reach = max(reach, stop)
        still = last >= end_day - timedelta(days=STILL_TRADING_DAYS)
        assets[cmc_id] = {"status": "mapped", "product": product, "first_candle": first.isoformat(),
                          "last_candle": None if still else last.isoformat()}
        report[cmc_id] = {"status": "mapped", "product": product, "first_candle": first.isoformat(),
                          "latest_candle_seen": last.isoformat(), "still_trading": still,
                          "first_at_search_start": first.isoformat() == results["search_start"],
                          "product_interval_gaps": gaps, "products": detail}
    return {"schema": LISTING_SCHEMA, "assets": assets}, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("--map", "--results", "--output-dir"):
        parser.add_argument(name, type=Path, required=True)
    parser.add_argument("--map-sha256", required=True)
    parser.add_argument("--results-sha256", required=True)
    args = parser.parse_args(argv)
    raw = {}
    for path, expected in ((args.map, args.map_sha256), (args.results, args.results_sha256)):
        raw[path] = path.read_bytes()
        if hashlib.sha256(raw[path]).hexdigest() != expected:
            raise SystemExit(f"pinned input changed or unexpected: {path}")
    listings, report = build(json.loads(raw[args.map]), json.loads(raw[args.results]), args.map_sha256)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with open(args.output_dir / "listings.json", "x") as stream:
        json.dump(listings, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with open(args.output_dir / "listings_report.json", "x") as stream:
        json.dump({"map_sha256": args.map_sha256, "results_sha256": args.results_sha256,
                   "still_trading_days": STILL_TRADING_DAYS, "assets": report}, stream, indent=2, sort_keys=True)
        stream.write("\n")
    counts = {}
    for rec in listings["assets"].values():
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    summary = {"assets": len(listings["assets"]), "status": counts,
               "listings_sha256": hashlib.sha256((args.output_dir / "listings.json").read_bytes()).hexdigest(),
               "assets_with_product_gaps": sorted(k for k, r in report.items() if r.get("product_interval_gaps"))}
    print(json.dumps(summary))
    return summary


if __name__ == "__main__":
    main()
