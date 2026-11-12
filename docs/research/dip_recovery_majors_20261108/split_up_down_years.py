"""Owner challenge 2026-11-08 ("old data during the period the market crashed"): the daily main-rule results split by
calendar years in which BTC rose or fell. Added after seeing the results, at the owner's prompt; hindsight split
(a year's direction is known only afterwards). Uses describe.py's own functions and the hash-listed daily files.
Usage: python3 -I -B split_up_down_years.py"""
import sys, json, datetime as dt, statistics
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import describe as D

F = (1 - 0.0005) * (1 - 0.005) / ((1 + 0.0005) * (1 + 0.005))   # as run: 0.50% + 0.05% slippage both sides
M = (1 - 0.0025) / ((1 + 0.0005) * (1 + 0.005))                  # buy 0.50% + slippage, sell 0.25% maker
UP = {2017, 2019, 2020, 2021, 2023, 2024}                          # BTC calendar-year change > 0 (results.json context)
day = D.sums(D.DAILY / "SHA256SUMS")
data = {}
for c in D.COINS:
    if D.sha(D.DAILY / f"{c}-USD.json") != day[f"{c}-USD.json"]:
        sys.exit(f"STOP: hash mismatch {c}")
    rows = json.load(open(D.DAILY / f"{c}-USD.json"))
    data[c] = D.Series([(r[0], r[3], r[2], r[1], r[4]) for r in rows], "daily")
yr = lambda t: dt.datetime.fromtimestamp(t[D.START], dt.timezone.utc).year


def stats(T):
    T = [t for t in T if not t[D.GAP] and t[D.FULL][30]]
    g = [t[D.EXITP] / t[D.ENTRY] for t in T]
    hit = sum(1 for t in T if t[D.K] is not None) / len(T)
    return len(T), 100 * hit, 100 * (F * statistics.fmean(g) - 1), 100 * (M * statistics.fmean(g) - 1), 100 * (statistics.fmean(g) - 1)


out = {"up": {}, "down": {}}
for y in D.YS:
    rnd = [t for S in data.values() for t in D.randoms(S, y, "touch")]
    for x in D.XS:
        ev = [t for S in data.values() for t in D.events(S, x, y, "touch")]
        for side, T in (("dip", ev), ("random", rnd)):
            for b, keep in (("up", lambda t: yr(t) in UP), ("down", lambda t: yr(t) not in UP)):
                out[b].setdefault((x, y), {})[side] = stats([t for t in T if keep(t)])
for b in ("up", "down"):
    print(f"== {b} years ({'BTC rose: 2017 2019 2020 2021 2023 2024' if b == 'up' else 'BTC fell: 2018 2022 2025 2026'}) ==")
    for i, lab in ((2, "as run 0.50%"), (3, "maker sell 0.25%"), (4, "no fees")):
        vals = [out[b][(x, y)]["dip"][i] for x in D.XS for y in D.YS]
        rv = [out[b][(x, y)]["random"][i] for x in D.XS for y in D.YS]
        print(f" {lab}: dips {min(vals):+.2f}..{max(vals):+.2f} pos {sum(v > 0 for v in vals)}/25 | random {min(rv):+.2f}..{max(rv):+.2f} pos {sum(v > 0 for v in rv)}/25")
    for (x, y) in ((3, 3), (3, 5), (5, 5), (1, 5)):
        d, r = out[b][(x, y)]["dip"], out[b][(x, y)]["random"]
        print(f"  -{x}/+{y}: dip n={d[0]} hit30={d[1]:.1f}% net050={d[2]:+.2f} maker={d[3]:+.2f} nofee={d[4]:+.2f} | random hit30={r[1]:.1f}% net050={r[2]:+.2f} nofee={r[4]:+.2f}")
