#!/usr/bin/env python3
"""Build a synthetic candles dir: python3 make_synthetic.py <out_dir> [seed]"""
import json
import math
import os
import random
import sys

out = sys.argv[1]
rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
os.makedirs(out, exist_ok=True)
D0 = 17167          # 2017-01-01
DEND = 20737        # 2026-10-11


def series(start, stop, p0, drift, vol, vol_usd, gap_p=0.0, gap_mondays=0.0):
    rows, p = [], p0
    for d in range(start, stop + 1):
        o = p
        p = max(1e-6, p * math.exp(drift + vol * rng.gauss(0, 1)))
        if rng.random() < gap_p:
            continue
        if gap_mondays and (d + 3) % 7 == 0 and rng.random() < gap_mondays:   # Mondays
            continue
        lo, hi = min(o, p) * 0.98, max(o, p) * 1.02
        rows.append([d * 86400, lo, hi, o, p, vol_usd * rng.uniform(0.5, 1.5) / p])
    return rows


files = {
    "BTC-USD": series(D0, DEND, 1000, 0.0012, 0.035, 5e8),
    "ETH-USD": series(D0, DEND, 10, 0.0015, 0.045, 3e8),
    "USDC-USD": series(D0, DEND, 1, 0, 0.0005, 9e9),          # excluded
    "WBTC-USD": series(D0, DEND, 1000, 0.0012, 0.035, 9e9),   # excluded
    "DEAD-USD": series(D0 + 300, 18700, 5, 0.004, 0.05, 4e8),   # delisted 2021-03-14 (never returns)
    "GAPPY-USD": series(D0 + 100, DEND, 3, 0.002, 0.06, 2e8, gap_p=0.03, gap_mondays=0.5),
    "LATE-USD": series(19500, 20300, 2, 0.003, 0.07, 3e8),      # listed 2023, delisted 2025
}
for i in range(25):
    s = rng.randint(D0, 20000)
    files[f"C{i:02d}-USD"] = series(s, DEND, rng.uniform(0.1, 50), rng.uniform(-0.002, 0.003),
                                    rng.uniform(0.03, 0.08), 10 ** rng.uniform(6, 8.5), gap_p=0.005)
# corrupt rows, duplicates, shuffle
for pid, rows in files.items():
    if rows:
        rows.append([rows[0][0] + 86400 * 5, 1, 1, 0, 1, 10])       # open <= 0, dropped
        rows.append([rows[0][0] + 86400 * 6, 1, 1, 1, None, 10])    # close missing, dropped
    rng.shuffle(rows)
    with open(os.path.join(out, pid + ".json"), "w") as f:
        json.dump(rows, f)
with open(os.path.join(out, "_products.json"), "w") as f:
    json.dump([{"id": k} for k in files], f)
print(out, len(files), "products")
