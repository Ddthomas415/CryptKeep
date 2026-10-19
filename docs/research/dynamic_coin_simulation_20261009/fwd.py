"""Event study, no costs: after a coin ranks in the top 3 by past gain, what does its price do over the next 1-48 hours?
Compared with the average eligible coin over the same hours. Uses hourly closes; decision at hour i uses closes < i."""
import json, sys, statistics
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3]]
src = open(sys.argv[0].replace("fwd.py", "short_hold.py")).read().split("def rotation")[0]
exec(src)
out = {}
FS = (1, 2, 4, 12, 24, 48)
for L in (1, 4, 24):
    ex = {F: [] for F in FS}
    for i in range(169, N - 48):
        rk = ranked(i, L)
        if len(rk) < 10: continue
        for F in FS:
            base = statistics.mean(close[p][i - 1 + F] / close[p][i - 1] - 1 for _, p in rk)
            for r, p in rk[:3]:
                if r > 0: ex[F].append((close[p][i - 1 + F] / close[p][i - 1] - 1) - base)
    for F in FS:
        e = ex[F]
        out[f"L{L}h_F{F}h"] = {"n": len(e), "mean_excess_pct": round(statistics.mean(e) * 100, 3), "median_excess_pct": round(statistics.median(e) * 100, 3), "share_positive_pct": round(100 * sum(1 for x in e if x > 0) / len(e), 1)}
    print(L, file=sys.stderr, flush=True)
print(json.dumps({"window": [START_S, END_S], "results": out}, indent=1))
