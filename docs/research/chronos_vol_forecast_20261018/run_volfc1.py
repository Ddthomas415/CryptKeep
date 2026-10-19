"""VOLFC-1 run script. Implements docs/research/chronos_vol_forecast_20261018/PREREGISTRATION.md
(frozen sha256 501723e7203da0ff975c9b97ae1514f90a18d0f44418da7e0c9ab0d92eca59e1) exactly.

Usage: python run_volfc1.py CANDLE_DIR MARKETS_CSV MODEL_DIR OUT_DIR
Coinbase candle rows: [unix_time, low, high, open, close, volume].
"""
import csv
import datetime as dt
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr

CANDLES, MARKETS, MODEL, OUT = map(Path, sys.argv[1:5])
FIRST_T, LAST_T = dt.date(2025, 10, 26), dt.date(2026, 10, 4)
TOP_N, LOOKBACK, CTX_MAX, H = 100, 60, 512, 7
QL = [0.1, 0.5, 0.9]
Z = 2.563103  # q0.9 - q0.1 of a standard normal
LAMBDA, EWMA_SEED = 0.94, 20
DELTA_MIN, BLOCK, NBOOT, SEED = 0.03, 4, 10_000, 20261018


def load():
    stable = {r["market"] for r in csv.DictReader(open(MARKETS))
              if r["venue"] == "coinbase" and r["asset_type_flag"] == "stable_or_wrapped"}
    data = {}
    for f in sorted(CANDLES.glob("*-USD.json")):
        market = f.name[:-5]
        if market in stable:
            continue
        rows = json.loads(f.read_bytes())
        by_day = {}
        for t, lo, hi, op, cl, vol in rows:
            d = dt.datetime.fromtimestamp(t, dt.timezone.utc).date()
            if d in by_day and by_day[d] != (cl, vol):
                raise SystemExit(f"conflicting duplicate {market} {d}")
            by_day[d] = (float(cl), float(vol))
        data[market] = by_day
    return data, stable


def contiguous_returns(by_day, t, max_n):
    """Log returns ending at t over the contiguous run of closes ending at t (at most max_n)."""
    closes, d = [], t
    while d in by_day and len(closes) < max_n + 1:
        closes.append(by_day[d][0]); d -= dt.timedelta(days=1)
    closes.reverse()
    return np.array([math.log(closes[k + 1] / closes[k]) for k in range(len(closes) - 1)])


def ewma_sigma(r):
    var = float(np.var(r[:EWMA_SEED], ddof=1))
    for x in r[EWMA_SEED:]:
        var = LAMBDA * var + (1 - LAMBDA) * x * x
    return math.sqrt(var)


def chronos_sigma(pipe, contexts):
    rows = []
    t0 = pd.Timestamp("2000-01-01")
    for i, r in enumerate(contexts):
        idx = pd.date_range(t0, periods=len(r), freq="D")
        rows.append(pd.DataFrame({"item_id": i, "timestamp": idx, "target": r.astype(np.float32)}))
    pred = pipe.predict_df(pd.concat(rows, ignore_index=True), prediction_length=H, quantile_levels=QL,
                           id_column="item_id", timestamp_column="timestamp", target="target",
                           cross_learning=False)
    out = []
    for i in range(len(contexts)):
        p = pred[pred["item_id"] == i]
        assert len(p) == H
        out.append(float(((p["0.9"] - p["0.1"]) / Z).mean()))
    return out


def main():
    from chronos import Chronos2Pipeline
    torch.manual_seed(0)
    data, stable = load()
    pipe = Chronos2Pipeline.from_pretrained(str(MODEL), device_map="cpu", torch_dtype=torch.float32)
    weeks, cells = [], []
    t = FIRST_T
    determinism = None
    while t <= LAST_T:
        cand = []
        for m, by_day in data.items():
            if all((t - dt.timedelta(days=k)) in by_day for k in range(LOOKBACK + 1)):
                dv = float(np.median([by_day[t - dt.timedelta(days=k)][0] * by_day[t - dt.timedelta(days=k)][1]
                                      for k in range(30)]))
                cand.append((dv, m))
        cand.sort(key=lambda x: (-x[0], x[1]))
        top = cand[:TOP_N]
        keep, dropped = [], 0
        for dv, m in top:
            by_day = data[m]
            if all((t + dt.timedelta(days=k)) in by_day for k in range(0, H + 1)):
                keep.append((dv, m))
            else:
                dropped += 1
        recs, contexts = [], []
        for dv, m in keep:
            by_day = data[m]
            r60 = contiguous_returns(by_day, t, LOOKBACK)
            assert len(r60) == LOOKBACK
            rctx = contiguous_returns(by_day, t, CTX_MAX)
            fut = [math.log(by_day[t + dt.timedelta(days=k + 1)][0] / by_day[t + dt.timedelta(days=k)][0])
                   for k in range(H)]
            recs.append({"market": m, "dollar_volume_median30": dv,
                         "realized": math.sqrt(sum(x * x for x in fut) / H),
                         "B1": float(np.std(r60, ddof=1)), "B2": ewma_sigma(rctx), "ctx_len": len(rctx)})
            contexts.append(rctx)
        sc = chronos_sigma(pipe, contexts)
        if determinism is None:
            determinism = sc == chronos_sigma(pipe, contexts)
            if not determinism:
                raise SystemExit("determinism check failed on week 1; stop per pre-registration")
        for rec, s in zip(recs, sc):
            rec["C"] = s
            rec["week"] = t.isoformat()
        cells.extend(recs)
        real = [r["realized"] for r in recs]
        w = {"t": t.isoformat(), "candidates": len(cand), "selected": len(top), "dropped": dropped,
             "used": len(recs)}
        for k in ("B1", "B2", "C"):
            w["rho_" + k] = float(spearmanr([r[k] for r in recs], real).statistic)
        weeks.append(w)
        print(w, flush=True)
        t += dt.timedelta(days=7)

    rho = {k: float(np.mean([w["rho_" + k] for w in weeks])) for k in ("B1", "B2", "C")}
    d = np.array([w["rho_C"] - w["rho_B1"] for w in weeks])
    rng = np.random.default_rng(SEED)
    n = len(d); nb = math.ceil(n / BLOCK)
    boots = np.empty(NBOOT)
    for b in range(NBOOT):
        starts = rng.integers(0, n - BLOCK + 1, size=nb)
        boots[b] = np.concatenate([d[s:s + BLOCK] for s in starts])[:n].mean()
    lower = float(np.quantile(boots, 0.05))
    delta = float(d.mean())
    c1, c2, c3 = delta >= DELTA_MIN, lower > 0, rho["C"] - rho["B2"] >= 0
    verdict = "PASS" if (c1 and c2 and c3) else "FAIL"

    def qlike(k):
        v = [(c["realized"] ** 2) / (c[k] ** 2) for c in cells if c["realized"] > 0]
        return float(np.mean([x - math.log(x) - 1 for x in v])), len(cells) - len(v)

    sec = {"qlike": {k: qlike(k)[0] for k in ("B1", "B2", "C")},
           "qlike_zero_realized_excluded": qlike("B1")[1],
           "weeks_rho_C_gt_B1": int(sum(w["rho_C"] > w["rho_B1"] for w in weeks)),
           "disclosed_sensitivity_excluding_week1_delta": float(d[1:].mean())}
    terc = {}
    for w in weeks:
        wc = sorted([c for c in cells if c["week"] == w["t"]], key=lambda c: -c["dollar_volume_median30"])
        k3 = len(wc) // 3
        for name, part in (("top", wc[:k3]), ("mid", wc[k3:2 * k3]), ("bottom", wc[2 * k3:])):
            real = [c["realized"] for c in part]
            for k in ("B1", "C"):
                terc.setdefault(f"{name}_{k}", []).append(float(spearmanr([c[k] for c in part], real).statistic))
    sec["rho_by_liquidity_tercile_mean"] = {k: float(np.nanmean(v)) for k, v in terc.items()}

    import chronos, transformers, scipy
    result = {
        "study": "VOLFC-1", "preregistration_sha256": "501723e7203da0ff975c9b97ae1514f90a18d0f44418da7e0c9ab0d92eca59e1",
        "run_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "verdict": verdict, "rho_mean": rho, "delta_C_minus_B1": delta, "bootstrap_lower_95_one_sided": lower,
        "rho_C_minus_B2": rho["C"] - rho["B2"], "criteria": {"delta_ge_0.03": c1, "lower_gt_0": c2, "C_ge_B2": c3},
        "weeks": len(weeks), "forecasts": len(cells), "stable_or_wrapped_excluded": len(stable),
        "secondary": sec, "determinism_week1_identical": determinism,
        "model": {"repo": "amazon/chronos-2", "revision": "29ec3766d36d6f73f0696f85560a422f50e8498c",
                  "model_safetensors_sha256": hashlib.sha256((MODEL / "model.safetensors").read_bytes()).hexdigest(),
                  "cross_learning": False, "device": "cpu", "dtype": "float32"},
        "versions": {"python": platform.python_version(), "torch": torch.__version__,
                     "chronos_forecasting": getattr(chronos, "__version__", "2.3.2"),
                     "transformers": transformers.__version__, "pandas": pd.__version__,
                     "numpy": np.__version__, "scipy": scipy.__version__},
        "run_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    pd.DataFrame(weeks).to_csv(OUT / "weekly.csv", index=False)
    pd.DataFrame(cells).to_csv(OUT / "forecasts.csv", index=False)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
