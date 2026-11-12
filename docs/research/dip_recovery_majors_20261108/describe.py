"""How long popular coins take to rise after a small dip. Descriptive, not a test: see PLAN.md (written before computing).
Usage: python3 -I describe.py SCRATCH [OUT_DIR]
SCRATCH holds cb/ and cb2/ extracted from docs/research/raw_archives_20261009/coinbase_hourly_last60d.tar.xz and
coinbase_hourly_prior10m.tar.xz. Every input is hash-checked before use. Standard library only.
Writes results.json and grid.csv to OUT_DIR (default: this folder), refusing to overwrite."""
import bisect, csv, datetime as dt, hashlib, itertools, json, statistics, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCH = ROOT / "docs/research/raw_archives_20261009"
DAILY = ROOT / "research/multisymbol_trend_20261015/data"
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "LTC", "DOT"]
XS = YS = (1, 2, 3, 4, 5)
FEES = (0.005, 0.012)
SLIP = 0.0005
HALF = int(dt.datetime(2026, 4, 9, tzinfo=dt.timezone.utc).timestamp())
CFG = {"hourly": {"step": 3600, "window": 720, "hz": (24, 168, 720), "gap_excl": False},
       "daily": {"step": 86400, "window": 30, "hz": (1, 7, 30), "gap_excl": True}}
ARCHIVE_SHA = {"coinbase_hourly_last60d.tar.xz": "435220c4d778036ba1b3e8ac78b7817f1a372bba1f5435d32c94af9c9bf5caa5",
               "coinbase_hourly_prior10m.tar.xz": "2bb417a2033b2a4b78df56db16c4471c6e1384ef23b433e276afb9108f99e6b4"}
# trade tuple fields
START, K, MAE, ENTRY, EXITP, FULL, GAP, END = range(8)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sums(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            h, name = line.split(maxsplit=1)
            out[name.strip().lstrip("*")] = h
    return out


def check_inputs(scratch):
    got = {}
    arch = sums(ARCH / "SHA256SUMS_archives.txt")
    for name, h in ARCHIVE_SHA.items():
        if arch.get(name) != h or sha(ARCH / name) != h:
            sys.exit(f"STOP: archive hash mismatch: {name}")
        got[f"docs/research/raw_archives_20261009/{name}"] = h
    inp, day = sums(ARCH / "SHA256SUMS_inputs.txt"), sums(DAILY / "SHA256SUMS")
    for c in COINS:
        for p in ("cb2", "cb"):
            rel = f"{p}/h1/{c}-USD.json"
            h = sha(scratch / rel)
            if inp.get(rel) != h:
                sys.exit(f"STOP: input hash mismatch: {rel}")
            got[f"SCRATCH/{rel}"] = h
        h = sha(DAILY / f"{c}-USD.json")
        if day.get(f"{c}-USD.json") != h:
            sys.exit(f"STOP: input hash mismatch: daily {c}")
        got[f"research/multisymbol_trend_20261015/data/{c}-USD.json"] = h
    return got


class Series:
    """Candles as (time, open, high, low, close), sorted; D = drop from the 24-hour high at each close."""

    def __init__(self, rows, kind):
        self.kind, self.step = kind, CFG[kind]["step"]
        rows = sorted(rows)
        self.ts = [int(r[0]) for r in rows]
        if len(set(self.ts)) != len(self.ts):
            sys.exit("STOP: duplicate candle times")
        self.o, self.h, self.l, self.c = ([float(r[k]) for r in rows] for k in (1, 2, 3, 4))
        n = self.n = len(rows)
        for i in range(n):
            if not (0 < self.l[i] <= min(self.o[i], self.c[i]) and self.h[i] >= max(self.o[i], self.c[i])):
                sys.exit(f"STOP: inconsistent candle at {self.ts[i]}")
        self.last = self.ts[-1]
        self.D = [None] * n
        for i in range(n):
            if kind == "hourly":
                if i >= 23 and self.ts[i] - self.ts[i - 23] == 23 * self.step:
                    self.D[i] = self.c[i] / max(self.h[i - 23:i + 1]) - 1
            else:
                self.D[i] = self.c[i] / self.h[i] - 1
        self.nextok = [i + 1 < n and self.ts[i + 1] == self.ts[i] + self.step for i in range(n)]


def trade(S, i, y, mode):
    """Start at the close of candle i; buy at the open of candle i+1; target y%; 30-day window."""
    cfg, step, ts, n = CFG[S.kind], S.step, S.ts, S.n
    e = i + 1
    entry = S.o[e]
    tgt = entry * (1 + y / 100)
    t_end = ts[e] + (cfg["window"] - 1) * step
    price = S.h if mode == "touch" else S.c
    low, lo, j, hit = S.l, float("inf"), e, None
    while j < n and ts[j] <= t_end:
        if low[j] < lo:
            lo = low[j]
        if price[j] >= tgt:
            hit = j
            break
        j += 1
    full = {H: ts[e] + (H - 1) * step <= S.last for H in cfg["hz"]}
    if hit is None:
        end, k = j - 1, None
        exitp = S.c[end] if full[cfg["window"]] else None
    else:
        end, k = hit, (ts[hit] - ts[e]) // step + 1
        exitp = tgt if mode == "touch" else (S.o[hit + 1] if hit + 1 < n else None)
    hi_t = min(t_end, S.last)
    gap = (bisect.bisect_right(ts, hi_t) - e) != (hi_t - ts[e]) // step + 1
    return (ts[i], k, lo / entry - 1, entry, exitp, full, gap, end)


def events(S, x, y, mode):
    out, after, thr = [], -1, -x / 100
    for i in range(1, S.n):
        if i <= after:
            continue
        d = S.D[i]
        if d is None or d > thr or not S.nextok[i]:
            continue
        if S.kind == "hourly" and (S.D[i - 1] is None or S.D[i - 1] <= thr):
            continue
        t = trade(S, i, y, mode)
        out.append(t)
        after = t[END]
        if after >= S.n - 1:
            break
    return out


def randoms(S, y, mode):
    return [trade(S, i, y, mode) for i in range(S.n) if S.D[i] is not None and S.nextok[i]]


def net(t, fee):
    return t[EXITP] * (1 - SLIP) * (1 - fee) / (t[ENTRY] * (1 + SLIP) * (1 + fee)) - 1


def pct(a, b):
    return round(100 * a / b, 2) if b else None


def summ(T, kind):
    cfg = CFG[kind]
    W = cfg["window"]
    ok = [t for t in T if not (cfg["gap_excl"] and t[GAP])]
    full = [t for t in ok if t[FULL][W]]
    s = {"events": len(T), "excluded_gap": len(T) - len(ok), "full_window": len(full),
         "open_at_data_end": sum(1 for t in ok if not t[FULL][W] and t[K] is None),
         "reached_window_incomplete": sum(1 for t in ok if not t[FULL][W] and t[K] is not None)}
    for H in cfg["hz"]:
        den = [t for t in ok if t[FULL][H]]
        num = sum(1 for t in den if t[K] is not None and t[K] <= H)
        s[f"within_{H}"] = [num, len(den), pct(num, len(den))]
    ks = [t[K] for t in full if t[K] is not None]
    s["median_time_reached"] = statistics.median(ks) if ks else None
    m = [t[MAE] for t in full]
    s["fell_further_median_pct"] = round(100 * statistics.median(m), 3) if m else None
    s["fell_further_worst_pct"] = round(100 * min(m), 3) if m else None
    for f in FEES:
        v = [net(t, f) for t in full if t[EXITP] is not None]
        s[f"net_fee_{f}"] = {"trades": len(v), "mean_pct": round(100 * statistics.fmean(v), 3) if v else None,
                             "positive_pct": pct(sum(1 for z in v if z > 0), len(v))}
    return s


def flat(lists):
    return list(itertools.chain.from_iterable(lists))


def sample(S, t, y, mode):
    i = S.ts.index(t[START])
    e = i + 1
    d = {"event_close_utc": iso(S.ts[i]), "close": S.c[i], "drop_pct": round(100 * S.D[i], 4),
         "entry_open_utc": iso(S.ts[e]), "entry": S.o[e], "target": round(S.o[e] * (1 + y / 100), 6),
         "mode": mode, "candles_to_target": t[K], "end_candle_utc": iso(S.ts[t[END]]),
         "lowest_low_pct": round(100 * t[MAE], 4), "exit": t[EXITP]}
    if S.kind == "hourly":
        d["high_24h"] = max(S.h[i - 23:i + 1])
    else:
        d["day_high"] = S.h[i]
    if t[EXITP] is not None and t[FULL][CFG[S.kind]["window"]]:
        d["net_pct_fee_0.005"] = round(100 * net(t, 0.005), 4)
    return d


def iso(v):
    return dt.datetime.fromtimestamp(v, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def main():
    t0 = time.time()
    scratch = Path(sys.argv[1])
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE
    hashes = check_inputs(scratch)
    data = {"hourly": {}, "daily": {}}
    for c in COINS:
        rows = json.load(open(scratch / "cb2/h1" / f"{c}-USD.json")) + json.load(open(scratch / "cb/h1" / f"{c}-USD.json"))
        data["hourly"][c] = Series([(r[0], r[1], r[2], r[3], r[4]) for r in rows], "hourly")
        rows = json.load(open(DAILY / f"{c}-USD.json"))  # Coinbase order: time, low, high, open, close, volume
        data["daily"][c] = Series([(r[0], r[3], r[2], r[1], r[4]) for r in rows], "daily")
    res = {"artifact_type": "research_only_descriptive_not_a_test", "plan_sha256": sha(HERE / "PLAN.md"),
           "script_sha256": sha(Path(__file__)), "inputs_sha256": hashes, "coverage": {}, "context": {},
           "hourly": {}, "daily": {}, "samples": []}
    for kind in data:
        res["coverage"][kind] = {c: {"candles": S.n, "first_utc": iso(S.ts[0]), "last_utc": iso(S.last),
                                     "missing_candles": (S.last - S.ts[0]) // S.step + 1 - S.n}
                                 for c, S in data[kind].items()}
    res["context"]["hourly_year_change_pct"] = {c: round(100 * (S.c[-1] / S.o[0] - 1), 2) for c, S in data["hourly"].items()}
    B = data["daily"]["BTC"]
    yrs = {}
    for i, v in enumerate(B.ts):
        yrs.setdefault(dt.datetime.fromtimestamp(v, dt.timezone.utc).year, []).append(i)
    res["context"]["btc_calendar_year_change_pct"] = {y: round(100 * (B.c[ix[-1]] / B.o[ix[0]] - 1), 2) for y, ix in yrs.items()}
    rows_csv = []
    for kind in ("hourly", "daily"):
        H0 = CFG[kind]["hz"][0]
        for mode in ("touch", "close"):
            for y in YS:
                rnd = {c: randoms(S, y, mode) for c, S in data[kind].items()}
                rs = {c: summ(rnd[c], kind) for c in COINS}
                rs["ALL"] = summ(flat(rnd.values()), kind)
                if kind == "hourly":
                    allr = flat(rnd.values())
                    rs_h = {"first": summ([t for t in allr if t[START] < HALF], kind),
                            "second": summ([t for t in allr if t[START] >= HALF], kind)}
                for x in XS:
                    ev = {c: events(S, x, y, mode) for c, S in data[kind].items()}
                    ds = {c: summ(ev[c], kind) for c in COINS}
                    alle = flat(ev.values())
                    ds["ALL"] = summ(alle, kind)
                    ahead = sum(1 for c in COINS if ds[c][f"within_{H0}"][2] is not None
                                and rs[c][f"within_{H0}"][2] is not None
                                and ds[c][f"within_{H0}"][2] > rs[c][f"within_{H0}"][2])
                    cell = {"dip": ds, "random": rs, f"coins_dip_more_often_within_{H0}": ahead}
                    if kind == "hourly":
                        cell["halves"] = {"dip": {"first": summ([t for t in alle if t[START] < HALF], kind),
                                                  "second": summ([t for t in alle if t[START] >= HALF], kind)},
                                          "random": rs_h}
                    if kind == "daily" and x == 3 and y == 3 and mode == "touch":
                        allr = flat(rnd.values())
                        by = {}
                        for side, T in (("dip", alle), ("random", allr)):
                            g = {}
                            for t in T:
                                g.setdefault(dt.datetime.fromtimestamp(t[START], dt.timezone.utc).year, []).append(t)
                            for yr, TT in sorted(g.items()):
                                by.setdefault(yr, {})[side] = summ(TT, kind)
                        cell["by_year"] = by
                    if x == 3 and y == 3 and mode == "touch":
                        res["samples"] += [dict(sample(data[kind]["BTC"], t, y, mode), kind=kind) for t in ev["BTC"][:3]]
                    if x == 3 and y == 3 and mode == "close":
                        res["samples"] += [dict(sample(data[kind]["BTC"], t, y, mode), kind=kind) for t in ev["BTC"][:1]]
                    res[kind].setdefault(mode, {})[f"X{x}_Y{y}"] = cell
                    for coin in COINS + ["ALL"]:
                        for side, s in (("dip", ds[coin]), ("random", rs[coin])):
                            rows_csv.append([kind, mode, coin, x, y, side, s["events"], s["excluded_gap"],
                                             s["open_at_data_end"]] + [s[f"within_{H}"][2] for H in CFG[kind]["hz"]]
                                            + [s["median_time_reached"], s["fell_further_median_pct"],
                                               s["fell_further_worst_pct"]]
                                            + [s[f"net_fee_{f}"][k] for f in FEES for k in ("mean_pct", "positive_pct")])
                print(f"{kind} {mode} Y{y} done {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    res["runtime_seconds"] = round(time.time() - t0, 1)
    with open(outdir / "results.json", "x") as fh:
        json.dump(res, fh, indent=1, allow_nan=False)
    with open(outdir / "grid.csv", "x", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["data", "mode", "coin", "drop_pct", "target_pct", "side", "events", "excluded_gap",
                    "open_at_data_end", "within_h1_pct", "within_h2_pct", "within_30d_pct", "median_time_reached",
                    "fell_further_median_pct", "fell_further_worst_pct", "net_mean_pct_fee050", "positive_pct_fee050",
                    "net_mean_pct_fee120", "positive_pct_fee120"])
        w.writerows(rows_csv)


if __name__ == "__main__":
    main()
