#!/usr/bin/env python3
"""Emit a fixed-cut FC-01-r1 input snapshot and availability ledger; no returns."""
import argparse
import bisect
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sqlite3


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db")
    args = parser.parse_args()
    cut = "2026-10-04T00:06:13+00:00"
    where = ("source='live_public' AND venue='coinbase' AND symbol='BTC/USD' "
             "AND capture_ts>=? AND capture_ts<=?")
    with sqlite3.connect(Path(args.db).resolve().as_uri() + "?mode=ro", uri=True) as con:
        con.execute("PRAGMA query_only=ON")
        con.execute("BEGIN")
        books = con.execute(
            "SELECT id,capture_ts,best_bid,best_ask,bid_notional,ask_notional,depth "
            f"FROM order_book_snapshots WHERE {where} ORDER BY capture_ts,id",
            ("2026-08-30", cut)).fetchall()
        quotes = con.execute(
            f"SELECT id,capture_ts,bid,ask FROM quote_snapshots WHERE {where} "
            "ORDER BY capture_ts,id", ("2026-08-30", cut)).fetchall()
    finite = lambda values: all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                and math.isfinite(x) for x in values)
    valid_quotes = [r for r in quotes if finite(r[2:]) and r[2] > 0 and r[3] >= r[2]]
    valid_books = [r for r in books if finite(r[2:]) and r[2] > 0
                   and r[3] >= r[2] and r[4] > 0 and r[5] > 0 and r[6] > 0]
    if not valid_books or not valid_quotes:
        raise ValueError("No valid book or quote input")
    bt = [dt.datetime.fromisoformat(r[1]) for r in valid_books]
    qt = [dt.datetime.fromisoformat(r[1]) for r in valid_quotes]
    boundary = bt[0].replace(hour=bt[0].hour // 6 * 6, minute=0, second=0, microsecond=0)
    if boundary < bt[0]:
        boundary += dt.timedelta(hours=6)
    windows = []
    while boundary + dt.timedelta(hours=6) <= min(bt[-1], qt[-1]):
        end = boundary + dt.timedelta(hours=6)
        i = bisect.bisect_right(bt, boundary) - 1
        # On equal capture times, the contract selects the lowest row ID.
        if i >= 0:
            i = bisect.bisect_left(bt, bt[i])
        j = bisect.bisect_left(qt, boundary)
        k = bisect.bisect_left(qt, end)
        feature_ok = i >= 0 and (boundary - bt[i]).total_seconds() <= 330
        entry_ok = j < len(qt) and (qt[j] - boundary).total_seconds() <= 330
        exit_ok = k < len(qt) and (qt[k] - end).total_seconds() <= 330
        qualifying = ((valid_books[i][4] - valid_books[i][5]) /
                      (valid_books[i][4] + valid_books[i][5]) >= 0.50) if feature_ok else None
        reasons = [name for name, ok in (("feature_unavailable", feature_ok),
                   ("entry_quote_unavailable", entry_ok), ("exit_quote_unavailable", exit_ok))
                   if not ok]
        windows.append(dict(boundary=boundary.isoformat(), exit_boundary=end.isoformat(),
                            book_id=valid_books[i][0] if feature_ok else None,
                            entry_quote_id=valid_quotes[j][0] if entry_ok else None,
                            exit_quote_id=valid_quotes[k][0] if exit_ok else None,
                            qualifying=qualifying, paired_eligible=not reasons,
                            exclusion_reasons=reasons))
        boundary = end
    inputs = dict(book_columns=["id", "capture_ts", "best_bid", "best_ask",
                               "bid_notional", "ask_notional", "depth"], books=books,
                  quote_columns=["id", "capture_ts", "bid", "ask"], quotes=quotes)
    result = dict(design="FC-01-r1", cut=cut, freshness_seconds=330, threshold=0.50,
                  input_content_sha256=digest(inputs), inputs=inputs, windows=windows,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  summary=dict(windows=len(windows),
                               paired_eligible=sum(w["paired_eligible"] for w in windows),
                               qualifying_complete=sum(w["paired_eligible"] and
                                                       w["qualifying"] for w in windows)))
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
