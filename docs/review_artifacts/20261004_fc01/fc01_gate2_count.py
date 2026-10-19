#!/usr/bin/env python3
"""FC-01 gate 2: count eligible six-hour windows and qualifying entries. NO returns.

Read-only (SQLite mode=ro + query_only). Reads timestamps, the validity
fields and the imbalance feature. Prices are read only to apply the draft's
validity rule (positive, finite, ask >= bid); no price difference, return or
outcome is computed anywhere in this file.

Usage:
  python3 fc01_gate2_count.py <crypto_edge_research.sqlite> [--until ISO_TS] [--limits 120,180,330,600,900]

--until pins the archive so the count is reproducible while the collector
keeps writing (default: 2026-10-04T00:06:13+00:00, the cut used in
docs/research/fc01_gate2_eligibility_count_20261004.md).
"""
import argparse, bisect, collections, datetime as dt, hashlib, math, sqlite3, sys

P = dt.datetime.fromisoformat
SINCE = "2026-08-30"
THRESHOLD = 0.50


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--until", default="2026-10-04T00:06:13+00:00")
    ap.add_argument("--limits", default="120,180,330,600,900")
    a = ap.parse_args(argv)
    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    where = "source='live_public' and venue='coinbase' and symbol='BTC/USD' and capture_ts>=? and capture_ts<=?"
    book = con.execute(
        f"select id, capture_ts, best_bid, best_ask, bid_notional, ask_notional, depth from order_book_snapshots where {where} order by capture_ts, id",
        (SINCE, a.until)).fetchall()
    quote = con.execute(
        f"select id, capture_ts, bid, ask from quote_snapshots where {where} order by capture_ts, id", (SINCE, a.until)).fetchall()
    fin = lambda *v: all(isinstance(x, (int, float)) and math.isfinite(x) for x in v)
    bvalid = lambda r: fin(*r[2:6]) and r[2] > 0 and r[3] > 0 and r[3] >= r[2] and r[4] > 0 and r[5] > 0 and bool(r[6]) and r[6] > 0
    qvalid = lambda r: fin(r[2], r[3]) and r[2] > 0 and r[3] > 0 and r[3] >= r[2]
    print(f"archive cut: capture_ts in [{SINCE}, {a.until}]")
    print(f"book rows {len(book)} (invalid {sum(not bvalid(r) for r in book)}), ids {book[0][0]}..{book[-1][0]}, first {book[0][1]}, last {book[-1][1]}")
    print(f"quote rows {len(quote)} (invalid {sum(not qvalid(r) for r in quote)}), ids {quote[0][0]}..{quote[-1][0]}")
    for name, rows in (("book", book), ("quote", quote)):
        h = hashlib.sha256("\n".join(f"{r[0]}|{r[1]}" for r in rows).encode()).hexdigest()
        print(f"{name} row-identity sha256 (id|capture_ts per line): {h}")
    book = [r for r in book if bvalid(r)]; quote = [r for r in quote if qvalid(r)]
    bt = [P(r[1]) for r in book]; qt = [P(r[1]) for r in quote]
    gaps = sorted((y - x).total_seconds() for x, y in zip(bt, bt[1:]))
    print(f"book cadence seconds: median {gaps[len(gaps)//2]:.0f}, p90 {gaps[int(len(gaps)*.9)]:.0f}, max {gaps[-1]:.0f}; gaps <= 120 s: {sum(g <= 120 for g in gaps)} of {len(gaps)}; gaps > 1 h: {sum(g > 3600 for g in gaps)}")
    first = bt[0].replace(minute=0, second=0, microsecond=0, hour=(bt[0].hour // 6) * 6)
    if first < bt[0]:
        first += dt.timedelta(hours=6)
    last = min(bt[-1], qt[-1])
    print(f"first boundary {first.isoformat()}, last usable capture {last.isoformat()}")
    print("limit_s | windows | feature_ok | outcome_quote_ok | both | qualifying(feature) | qualifying+outcome | +entry_quote")
    for lim in [int(x) for x in a.limits.split(",")]:
        c = collections.Counter(); b = first
        while b + dt.timedelta(hours=6) <= last:
            nb = b + dt.timedelta(hours=6); c["w"] += 1
            i = bisect.bisect_right(bt, b) - 1
            f = i >= 0 and (b - bt[i]).total_seconds() <= lim
            j = bisect.bisect_left(qt, nb); e = j < len(qt) and (qt[j] - nb).total_seconds() <= lim
            k = bisect.bisect_left(qt, b); en = k < len(qt) and (qt[k] - b).total_seconds() <= lim
            c["f"] += f; c["e"] += e; c["fe"] += f and e
            if f:
                q = (book[i][4] - book[i][5]) / (book[i][4] + book[i][5]) >= THRESHOLD
                c["q"] += q; c["qe"] += q and e; c["qee"] += q and e and en
            b = nb
        print(f"{lim:7d} | {c['w']:7d} | {c['f']:10d} | {c['e']:16d} | {c['fe']:4d} | {c['q']:19d} | {c['qe']:18d} | {c['qee']:12d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
