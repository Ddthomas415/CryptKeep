"""CMC statistical method v3 - SIZE-ONLY certification (operator decision 2026-10-09). Synthetic data only.

Plan: docs/research/cmc_trending_log/statistical_method_v3_PLAN_20261009.md (approved; power bar replaced by
size-only certification after oracle_power_bound_20261009.py showed the v2 power bar is unattainable).
Estimand: day-weighted mean (each entry day once) of observed event excess returns.
Candidates (fixed before any run): A fixed-b Bartlett HAC t-test (b=0.2, Kiefer-Vogelsang one-sided 95% critical
value polynomial); B studentized circular block bootstrap (block 14 days, 2000 resamples); C non-overlapping weekly
t-test (days 0, 7, 14, ...). Decision = one-sided 95% lower bound > 0 (equivalent to the 90% two-sided range above 0).
The generator below is a verbatim copy of cmc_calibration_models.generate with NEW stage labels (new seeds); a test
proves byte-identical output to v2 when given a v2 stage label.
"""
import hashlib
import json
import math

import numpy as np

MODELS = ("iid", "overlap7", "persistent", "heavy_tail", "volatility_shift",
          "shared_unequal", "sparse", "random_missing", "loss_missing")
SUPPORTED = MODELS[:6]
STREAMS = ("innovations", "event_noise", "counts", "missingness", "bootstrap", "heavy_tail_denominator")
MEANS = (0., .0025, .005, .01)
STAGES = ("v3_development", "v3_confirmation")
METHODS = ("C_weekly_t", "B_studentized_circular_block14", "A_fixed_b_hac")  # tie order C, B, A
B_RESAMPLES, BLOCK, FIXED_B = 2000, 14, 0.2


def stream_seed(stage, model, days, mean_index, trial, stream, allowed=STAGES):
    if stage not in allowed:
        raise ValueError("unknown stage")
    if model not in MODELS or stream not in STREAMS:
        raise ValueError("unknown model or stream")
    if days not in (90, 180, 365) or mean_index not in range(4) or trial < 0:
        raise ValueError("invalid history identifier")
    encoded = json.dumps([stage, model, days, mean_index, trial, stream],
                         ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return int.from_bytes(hashlib.sha256(encoded).digest()[:16], "big")


def generate(stage, model, days, mean_index, trial, allowed=STAGES):
    def rng(stream):
        return np.random.Generator(np.random.PCG64(
            stream_seed(stage, model, days, mean_index, trial, stream, allowed)))
    innovations = rng("innovations")
    z = innovations.standard_normal(days+6)
    mu, sigma = MEANS[mean_index], .03
    if model == "heavy_tail":
        v = rng("heavy_tail_denominator").standard_normal((days+6, 5))
        z = z/np.sqrt(np.mean(v*v, axis=1))*np.sqrt(3/5)
    if model == "iid":
        shocks = sigma*z[:days]
    elif model == "persistent":
        state = sigma*innovations.standard_normal()
        shocks = np.empty(days)
        for t in range(days):
            state = .85*state+sigma*np.sqrt(1-.85**2)*z[t]
            shocks[t] = state
    else:
        scales = np.full(days+6, sigma)
        if model == "volatility_shift":
            scales[days//2:] *= 3
        shocks = np.convolve(z*scales, np.ones(7), mode="valid")/np.sqrt(7)
    counts = np.ones(days, dtype=int)
    if model == "shared_unequal":
        counts[days//2] = 20
    if model == "sparse":
        counts = (rng("counts").random(days) < .2).astype(int)
    day_index = np.repeat(np.arange(days), counts)
    truth = mu+shocks[day_index]
    if model == "shared_unequal":
        truth = truth+.01*rng("event_noise").standard_normal(len(truth))
    observed = np.ones(len(truth), dtype=bool)
    if model in ("random_missing", "loss_missing"):
        probability = .2 if model == "random_missing" else np.where(truth < 0, .8, .1)
        observed = rng("missingness").random(len(truth)) >= probability
    return {"day_index": day_index, "truth": truth, "observed": observed,
            "days": days, "refusal_only": model in MODELS[6:],
            "numpy_version": np.__version__}


def day_series(history):
    """Day-weighted series; refusal-only models and any day without an observed event refuse inference."""
    if history["refusal_only"]:
        return None
    obs = history["observed"]
    days = history["days"]
    totals = np.bincount(history["day_index"][obs], weights=history["truth"][obs], minlength=days)
    counts = np.bincount(history["day_index"][obs], minlength=days)
    if (counts == 0).any():
        return None
    return totals/counts


def _betacf(a, b, x):
    qab, qap, qam = a+b, a+1, a-1
    c, d = 1., 1.-qab*x/qap
    d = 1./(d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 300):
        m2 = 2*m
        aa = m*(b-m)*x/((qam+m2)*(a+m2))
        d = 1.+aa*d; d = 1./(d if abs(d) > 1e-300 else 1e-300)
        c = 1.+aa/c if abs(1.+aa/c) > 1e-300 else 1e-300
        h *= d*c
        aa = -(a+m)*(qab+m)*x/((a+m2)*(qap+m2))
        d = 1.+aa*d; d = 1./(d if abs(d) > 1e-300 else 1e-300)
        c = 1.+aa/c if abs(1.+aa/c) > 1e-300 else 1e-300
        delta = d*c
        h *= delta
        if abs(delta-1.) < 1e-14:
            break
    return h


def t_cdf(t, df):
    x = df/(df+t*t)
    lbeta = math.lgamma(df/2)+math.lgamma(.5)-math.lgamma(df/2+.5)
    front = math.exp(math.log(x)*df/2+math.log(1-x)*.5-lbeta)
    a, b = df/2, .5
    if x < (a+1)/(a+b+2):
        ibeta = front*_betacf(a, b, x)/a
    else:
        ibeta = 1.-math.exp(math.log(1-x)*b+math.log(x)*a-lbeta)*_betacf(b, a, 1-x)/b
    return 1.-.5*ibeta if t > 0 else .5*ibeta


def t_quantile_95(df):
    lo, hi = 0., 50.
    for _ in range(200):
        mid = (lo+hi)/2
        if t_cdf(mid, df) < .95:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2


def kv_critical(b=FIXED_B):
    return 1.6449+2.1859*b+.3142*b*b-.3427*b**3


def method_A(y):
    n = len(y)
    m = max(1, int(FIXED_B*n))
    d = y-y.mean()
    ac = np.array([d[:n-j] @ d[j:] / n for j in range(m)])
    lrv = ac[0]+2*np.sum(ac[1:]*(1-np.arange(1, m)/m))
    if not lrv > 0:
        return {"status": "UNAVAILABLE"}
    se = math.sqrt(lrv/n)
    return {"status": "AVAILABLE", "lower": float(y.mean()-kv_critical()*se)}


def method_B(y, rng):
    n = len(y)
    k = n//BLOCK
    if k < 2:
        return {"status": "UNAVAILABLE"}
    ext = np.concatenate([y, y[:BLOCK-1]])
    block_means = np.convolve(ext, np.ones(BLOCK), mode="valid")[:n]/BLOCK   # all n circular blocks
    se = math.sqrt(block_means.var()/k)
    if not se > 0:
        return {"status": "UNAVAILABLE"}
    draws = block_means[rng.integers(0, n, size=(B_RESAMPLES, k))]
    star_mean, star_se = draws.mean(1), draws.std(1, ddof=1)/math.sqrt(k)
    ok = star_se > 0
    tstar = (star_mean[ok]-block_means.mean())/star_se[ok]
    if len(tstar) < B_RESAMPLES:
        return {"status": "UNAVAILABLE"}
    q = np.sort(tstar)[int(math.floor(.95*B_RESAMPLES))]
    return {"status": "AVAILABLE", "lower": float(y.mean()-q*se)}


def method_C(y):
    w = y[::7]
    k = len(w)
    if k < 3:
        return {"status": "UNAVAILABLE"}
    sd = w.std(ddof=1)
    if not sd > 0:
        return {"status": "UNAVAILABLE"}
    return {"status": "AVAILABLE", "lower": float(w.mean()-t_quantile_95(k-1)*sd/math.sqrt(k))}


def evaluate(method, stage, model, days, mean_index, trial):
    y = day_series(generate(stage, model, days, mean_index, trial))
    if y is None:
        return {"status": "REFUSED"}
    if method == "A_fixed_b_hac":
        r = method_A(y)
    elif method == "B_studentized_circular_block14":
        rng = np.random.Generator(np.random.PCG64(stream_seed(stage, model, days, mean_index, trial, "bootstrap")))
        r = method_B(y, rng)
    elif method == "C_weekly_t":
        r = method_C(y)
    else:
        raise ValueError("unknown method")
    if r["status"] == "AVAILABLE":
        r["positive"] = r["lower"] > 0
    return r


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (None, None)
    p = k/n
    den = 1+z*z/n
    centre = (p+z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (centre-half, centre+half)
