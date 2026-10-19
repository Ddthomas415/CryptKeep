"""Offline coverage counts only. No forecasts, strategy scores or network calls."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from statistics import median

COLUMNS = {
    "funding_snapshots": ("funding_rate", "interval_hours"),
    "basis_snapshots": ("spot_px", "perp_px", "days_to_expiry"),
    "open_interest_snapshots": ("open_interest",),
    "quote_snapshots": ("bid", "ask"),
    "order_book_snapshots": ("best_bid", "best_ask", "bid_notional", "ask_notional"),
}
COMMON = ("id", "source", "venue", "symbol", "capture_ts")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def timestamp(value):
    date = datetime.fromisoformat(value)
    if date.tzinfo is None:
        raise ValueError("naive_capture_timestamp")
    return date.timestamp()


def capture(db):
    # Do not instantiate the application store: it initializes schema/WAL settings.
    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        tables = {table: [dict(row) for row in conn.execute(
            f"SELECT {','.join(COMMON + fields)} FROM {table} ORDER BY id")]
            for table, fields in COLUMNS.items()}
        assert conn.total_changes == 0
    return {"captured_utc": datetime.now(timezone.utc).isoformat(),
            "source": str(db.resolve()), "tables": tables}


def valid(table, row):
    def number(key, *, positive=False):
        value = row.get(key)
        return (type(value) in (int, float) and math.isfinite(value)
                and (value > 0 if positive else value >= 0))

    try:
        timestamp(row["capture_ts"])
    except (KeyError, TypeError, ValueError):
        return False
    if table == "funding_snapshots":
        value = row.get("funding_rate")
        return (type(value) in (int, float) and math.isfinite(value)
                and number("interval_hours", positive=True))
    if table == "basis_snapshots":
        return number("spot_px", positive=True) and number("perp_px", positive=True)
    if table == "open_interest_snapshots":
        return number("open_interest")
    if table == "quote_snapshots":
        return number("bid", positive=True) and number("ask", positive=True) and row["bid"] <= row["ask"]
    return (number("best_bid", positive=True) and number("best_ask", positive=True)
            and row["best_bid"] <= row["best_ask"] and number("bid_notional") and number("ask_notional"))


def summarize(rows):
    times = sorted({timestamp(r["capture_ts"]) for r in rows})
    differences = [b - a for a, b in zip(times, times[1:])]
    return {"rows": len(rows), "unique_capture_times": len(times),
            "duplicate_capture_rows": len(rows) - len(times),
            "first_utc": datetime.fromtimestamp(times[0], timezone.utc).isoformat() if times else None,
            "last_utc": datetime.fromtimestamp(times[-1], timezone.utc).isoformat() if times else None,
            "utc_days_present": len({datetime.fromtimestamp(t, timezone.utc).date() for t in times}),
            "median_spacing_seconds": median(differences) if differences else None,
            "largest_gap_hours": max(differences) / 3600 if differences else None,
            "gaps_over_600_seconds": sum(d > 600 for d in differences),
            "gaps_over_24_hours": sum(d > 86400 for d in differences)}


def asof_count(anchors, contexts, max_age=300):
    ordered = [sorted(set(group)) for group in contexts]
    matched = 0
    for anchor in anchors:
        for group in ordered:
            index = bisect_right(group, anchor) - 1
            if index < 0 or anchor - group[index] > max_age:
                break
        else:
            matched += 1
    return matched


def audit_projection(projection):
    groups = []
    eligible = {}
    excluded = {}
    for table, rows in projection["tables"].items():
        live = [r for r in rows if r["source"] == "live_public"]
        excluded[table] = dict(Counter(r["source"] for r in rows if r["source"] != "live_public"))
        eligible[table] = [r for r in live if valid(table, r)]
        grouped = defaultdict(list)
        for row in live:
            grouped[row["venue"], row["symbol"]].append(row)
        for (venue, symbol), items in sorted(grouped.items()):
            good = [r for r in items if valid(table, r)]
            groups.append({"table": table, "venue": venue, "symbol": symbol,
                           "invalid_rows": len(items) - len(good), **summarize(good)})
    anchors = sorted({timestamp(r["capture_ts"]) for r in eligible["quote_snapshots"]
                      if (r["venue"], r["symbol"]) == ("coinbase", "BTC/USD")})
    contexts = [[timestamp(r["capture_ts"]) for r in eligible[t]
                 if (r["venue"], r["symbol"]) == ("okx", "BTC/USDT:USDT")]
                for t in ("funding_snapshots", "basis_snapshots", "open_interest_snapshots")]
    return {"groups": groups, "excluded_non_live_sources": excluded,
            "btc_context_capture_join": {"quote_times": len(anchors), "max_age_seconds": 300,
                "funding_basis_oi_at_or_before_quote": asof_count(anchors, contexts),
                "meaning": "Capture-time coverage only; cross-venue USD/USDT references, not executable prices or settled funding"}}


def audit_funding(raw):
    grouped = defaultdict(list)
    kinds = Counter()
    for line in raw.decode().splitlines():
        row = json.loads(line)
        kinds[row["type"]] += 1
        if row["type"] == "funding":
            rate = float(row["fundingRate"])
            if not math.isfinite(rate):
                raise ValueError("invalid_funding_rate")
            grouped[row["symbol"]].append(row)
    output = {}
    for symbol, rows in sorted(grouped.items()):
        seen = {}
        for row in rows:
            time = int(row["fundingTime"])
            if time in seen and seen[time] != row:
                raise ValueError("conflicting_funding_records")
            seen[time] = row
        ordered = sorted(seen)
        output[symbol] = {"rows": len(rows), "unique_settlement_timestamps": len(seen),
            "duplicate_rows": len(rows) - len(seen),
            "first_utc": datetime.fromtimestamp(ordered[0] / 1000, timezone.utc).isoformat(),
            "last_utc": datetime.fromtimestamp(ordered[-1] / 1000, timezone.utc).isoformat(),
            "missing_mark_price_rows": sum(not r.get("markPrice") for r in seen.values()),
            "before_recorded_E7_target_window": sum(t < 1606780800000 for t in ordered),
            "median_spacing_seconds": median((b-a)/1000 for a, b in zip(ordered, ordered[1:])) if len(ordered) > 1 else None,
            "gaps_over_9_hours": sum(b-a > 9*3600*1000 for a, b in zip(ordered, ordered[1:]))}
    return {"record_types": dict(kinds), "symbols": output,
            "warning": "Pre-December-2020 count is not untouched evidence; historical data already inspected. No data authenticity or payout proof."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--projection", type=Path)
    parser.add_argument("--funding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.db is None) == (args.projection is None):
        parser.error("provide exactly one of --db or --projection")
    projection = capture(args.db) if args.db else json.loads(args.projection.read_bytes())
    raw = args.funding.read_bytes()
    report = {"projection_sha256": hashlib.sha256(canonical(projection)).hexdigest(),
              "funding_sha256": hashlib.sha256(raw).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "captured_utc": projection["captured_utc"],
              "context": audit_projection(projection), "historical_funding": audit_funding(raw),
              "status_events": "UNKNOWN: no verified incident ledger in the inspected five-table store; not zero events"}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "projection.json").write_bytes(canonical(projection))
    (args.output / "counts.json").write_bytes(canonical(report))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
